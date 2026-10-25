#include <android_native_app_glue.h>
#include <android/asset_manager.h>
#include <android/input.h>
#include <android/log.h>
#include <android/native_window.h>
#include <android/window.h>
#include <aaudio/AAudio.h>
#include <jni.h>
#include "surface/session.hpp"
#include "surface/engine_service.hpp"
#include "surface/checkpoint.hpp"
#include "surface/atlas.hpp"
#include "surface/acoustic.hpp"
#include "surface/input.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <memory>
#include <mutex>
#include <string>
#include <vector>
#include <unistd.h>
#include <fcntl.h>
#include <poll.h>
#include <cerrno>

namespace {
using namespace surface;
using Clock=std::chrono::steady_clock;
std::atomic<int> uiWidth{0},uiHeight{0};
std::mutex importMutex;
std::string importUri;
void log(const std::string& text){__android_log_print(ANDROID_LOG_INFO,"Surface","%s",text.c_str());}

struct Jni {
 ANativeActivity* activity;JNIEnv* env=nullptr;bool attached=false;
 explicit Jni(ANativeActivity* a):activity(a){if(a->vm->GetEnv(reinterpret_cast<void**>(&env),JNI_VERSION_1_6)!=JNI_OK){if(a->vm->AttachCurrentThread(&env,nullptr)==JNI_OK)attached=true;}if(env)env->PushLocalFrame(64);}
 ~Jni(){if(env){if(env->ExceptionCheck()){env->ExceptionClear();log("Android platform operation failed");}env->PopLocalFrame(nullptr);}if(attached)activity->vm->DetachCurrentThread();}
 bool ok()const{return env&&!env->ExceptionCheck();}
};
void immersive(ANativeActivity* activity){
 // This NDK function posts to the Activity UI thread. All View/Window JNI mutations
 // live exclusively in SurfaceActivity.java's UI-thread lifecycle callbacks.
 ANativeActivity_setWindowFlags(activity,AWINDOW_FLAG_FULLSCREEN|AWINDOW_FLAG_KEEP_SCREEN_ON,0);
}
std::pair<int,int> windowExtent(ANativeWindow* native){
 const int w=uiWidth.load(),h=uiHeight.load();if(w>0&&h>0)return {w,h};return {ANativeWindow_getWidth(native),ANativeWindow_getHeight(native)};
}
std::vector<std::uint8_t> asset(ANativeActivity* a,const char* path){
 AAsset* file=AAssetManager_open(a->assetManager,path,AASSET_MODE_BUFFER);if(!file)throw std::runtime_error("missing packaged asset");const auto length=AAsset_getLength64(file);
 if(length<0||length>32*1024*1024){AAsset_close(file);throw std::runtime_error("asset size limit");}
 std::vector<std::uint8_t> data(std::size_t(length),0);std::size_t done=0;while(done<data.size()){const int n=AAsset_read(file,data.data()+done,data.size()-done);if(n<=0){AAsset_close(file);throw std::runtime_error("asset truncated");}done+=n;}AAsset_close(file);return data;
}

bool exportToDownloads(ANativeActivity* activity,std::span<const std::byte> data,const std::string& name){
 // Android 10+ permits an app to create its own Downloads entry without a storage permission.
 Jni j(activity);if(!j.env)return false;auto e=j.env;
 auto ac=e->GetObjectClass(activity->clazz);auto resolver=e->CallObjectMethod(activity->clazz,e->GetMethodID(ac,"getContentResolver","()Landroid/content/ContentResolver;"));
 auto cv=e->FindClass("android/content/ContentValues");auto values=e->NewObject(cv,e->GetMethodID(cv,"<init>","()V"));auto put=e->GetMethodID(cv,"put","(Ljava/lang/String;Ljava/lang/String;)V");
 auto value=[&](const char* k,const std::string& v){auto key=e->NewStringUTF(k),str=e->NewStringUTF(v.c_str());e->CallVoidMethod(values,put,key,str);e->DeleteLocalRef(key);e->DeleteLocalRef(str);};
 value("_display_name",name);value("mime_type","application/x-surface-checkpoint");value("relative_path","Download/Surface");
 auto integer=e->FindClass("java/lang/Integer");auto one=e->CallStaticObjectMethod(integer,e->GetStaticMethodID(integer,"valueOf","(I)Ljava/lang/Integer;"),1);auto pending=e->NewStringUTF("is_pending");auto putInt=e->GetMethodID(cv,"put","(Ljava/lang/String;Ljava/lang/Integer;)V");e->CallVoidMethod(values,putInt,pending,one);
 auto downloads=e->FindClass("android/provider/MediaStore$Downloads");auto collection=e->GetStaticObjectField(downloads,e->GetStaticFieldID(downloads,"EXTERNAL_CONTENT_URI","Landroid/net/Uri;"));
 auto rc=e->GetObjectClass(resolver);auto uri=e->CallObjectMethod(resolver,e->GetMethodID(rc,"insert","(Landroid/net/Uri;Landroid/content/ContentValues;)Landroid/net/Uri;"),collection,values);if(!j.ok()||!uri)return false;
 auto mode=e->NewStringUTF("w");auto descriptor=e->CallObjectMethod(resolver,e->GetMethodID(rc,"openFileDescriptor","(Landroid/net/Uri;Ljava/lang/String;)Landroid/os/ParcelFileDescriptor;"),uri,mode);if(!j.ok()||!descriptor)return false;auto dc=e->GetObjectClass(descriptor);const int fd=e->CallIntMethod(descriptor,e->GetMethodID(dc,"getFd","()I"));if(!j.ok()||fd<0)return false;
 std::size_t done=0;while(done<data.size()){const auto n=write(fd,data.data()+done,data.size()-done);if(n<=0)break;done+=std::size_t(n);}const bool saved=done==data.size()&&fsync(fd)==0;e->CallVoidMethod(descriptor,e->GetMethodID(dc,"close","()V"));
 if(saved){e->CallVoidMethod(values,e->GetMethodID(cv,"clear","()V"));auto zero=e->CallStaticObjectMethod(integer,e->GetStaticMethodID(integer,"valueOf","(I)Ljava/lang/Integer;"),0);e->CallVoidMethod(values,putInt,pending,zero);e->CallIntMethod(resolver,e->GetMethodID(rc,"update","(Landroid/net/Uri;Landroid/content/ContentValues;Ljava/lang/String;[Ljava/lang/String;)I"),uri,values,nullptr,nullptr);}
 else e->CallIntMethod(resolver,e->GetMethodID(rc,"delete","(Landroid/net/Uri;Ljava/lang/String;[Ljava/lang/String;)I"),uri,nullptr,nullptr);
 return saved&&j.ok();
}

std::vector<std::byte> readDocument(ANativeActivity* activity,const std::string& path){
 if(path.size()>8192)throw std::invalid_argument("document URI budget");
 Jni j(activity);if(!j.env)throw std::runtime_error("Android document service unavailable");auto e=j.env;
 auto ac=e->GetObjectClass(activity->clazz);auto resolver=e->CallObjectMethod(activity->clazz,e->GetMethodID(ac,"getContentResolver","()Landroid/content/ContentResolver;"));if(!j.ok()||!resolver)throw std::runtime_error("document resolver unavailable");
 auto uc=e->FindClass("android/net/Uri");auto text=e->NewStringUTF(path.c_str());auto uri=e->CallStaticObjectMethod(uc,e->GetStaticMethodID(uc,"parse","(Ljava/lang/String;)Landroid/net/Uri;"),text);if(!j.ok()||!uri)throw std::runtime_error("invalid document URI");
 auto rc=e->GetObjectClass(resolver);auto mode=e->NewStringUTF("r");auto descriptor=e->CallObjectMethod(resolver,e->GetMethodID(rc,"openFileDescriptor","(Landroid/net/Uri;Ljava/lang/String;)Landroid/os/ParcelFileDescriptor;"),uri,mode);if(!j.ok()||!descriptor)throw std::runtime_error("document access denied");
 auto dc=e->GetObjectClass(descriptor);const int fd=e->CallIntMethod(descriptor,e->GetMethodID(dc,"getFd","()I"));if(!j.ok()||fd<0)throw std::runtime_error("invalid document descriptor");
 std::vector<std::byte> bytes;std::array<std::byte,65536> buffer{};bool eof=false;const auto deadline=Clock::now()+std::chrono::seconds(2);const int flags=fcntl(fd,F_GETFL);if(flags>=0)fcntl(fd,F_SETFL,flags|O_NONBLOCK);
 while(Clock::now()<deadline&&bytes.size()<=10*1024*1024+80){
  pollfd ready{fd,POLLIN,0};const int status=poll(&ready,1,100);if(status<0&&errno==EINTR)continue;if(status<0)break;if(!status)continue;
  const auto n=read(fd,buffer.data(),buffer.size());if(n==0){eof=true;break;}if(n<0){if(errno==EAGAIN||errno==EINTR)continue;break;}bytes.insert(bytes.end(),buffer.begin(),buffer.begin()+n);
 }
 e->CallVoidMethod(descriptor,e->GetMethodID(dc,"close","()V"));
 if(!eof||bytes.size()>10*1024*1024+80)throw std::runtime_error("document read incomplete or oversized");return bytes;
}

class Sound {
 std::mutex mutex_;std::unique_ptr<AcousticField> field_;AAudioStream* stream_=nullptr;std::atomic<bool> enabled_{false};
 static aaudio_data_callback_result_t callback(AAudioStream*,void* user,void* buffer,int32_t frames){
  auto& s=*static_cast<Sound*>(user);auto pcm=std::span<float>(static_cast<float*>(buffer),std::size_t(frames));std::unique_lock lock(s.mutex_,std::try_to_lock);
  if(lock&&s.enabled_.load()&&s.field_)s.field_->render(pcm);else std::fill(pcm.begin(),pcm.end(),0);return AAUDIO_CALLBACK_RESULT_CONTINUE;
 }
public:
 ~Sound(){if(stream_){AAudioStream_requestStop(stream_);AAudioStream_close(stream_);}}
 void enable(bool enabled){
  if(enabled&&!stream_){AAudioStreamBuilder* b=nullptr;if(AAudio_createStreamBuilder(&b)!=AAUDIO_OK)return;AAudioStreamBuilder_setDirection(b,AAUDIO_DIRECTION_OUTPUT);AAudioStreamBuilder_setFormat(b,AAUDIO_FORMAT_PCM_FLOAT);AAudioStreamBuilder_setChannelCount(b,1);AAudioStreamBuilder_setSampleRate(b,48000);AAudioStreamBuilder_setPerformanceMode(b,AAUDIO_PERFORMANCE_MODE_LOW_LATENCY);AAudioStreamBuilder_setDataCallback(b,callback,this);
   const auto result=AAudioStreamBuilder_openStream(b,&stream_);AAudioStreamBuilder_delete(b);if(result!=AAUDIO_OK){stream_=nullptr;log("Audio device unavailable");return;}field_=std::make_unique<AcousticField>(AAudioStream_getSampleRate(stream_));AAudioStream_requestStart(stream_);
  }enabled_.store(enabled);
 }
 void strike(float x,float y,float pressure){std::unique_lock lock(mutex_,std::try_to_lock);if(lock&&field_)field_->strike(x,y,std::clamp(pressure,-3.f,3.f));}
};

struct Application {
 android_app* host=nullptr;Session session;std::unique_ptr<EngineService> engine;std::unique_ptr<Renderer> renderer;atlas::Catalogue catalogue;Sound sound;
 std::uint64_t sequence=0;int physicalWidth=1,physicalHeight=1,peakPointers=0;float lastX=.5f,lastY=.5f,pinch=0;double moved=0;bool focused=false,gesture=false;
 Clock::time_point gestureStart=Clock::now(),lastTap=Clock::now()-std::chrono::seconds(5),lastFrame=Clock::now();std::filesystem::path checkpointPath;
 explicit Application(android_app* app):host(app),session(112,160),checkpointPath(std::filesystem::path(app->activity->internalDataPath)/"checkpoints"){
  try{
   CheckpointStore store(checkpointPath);const auto candidates=store.loadCandidates();
   for(const auto& saved:candidates){try{session.restore(std::span<const std::byte>(reinterpret_cast<const std::byte*>(saved.payload.data()),saved.payload.size()));session.view.generation=candidates.front().generation;log("Restored valid checkpoint "+std::to_string(saved.generation));break;}catch(const std::exception& e){log(std::string("Rejected checkpoint payload: ")+e.what());}}
  }catch(const std::exception& e){log(std::string("Checkpoint admission: ")+e.what());}
  try{catalogue=atlas::loadCatalogue(asset(app->activity,"gaia.bin"));}catch(const std::exception& e){log(e.what());}
  engine=std::make_unique<EngineService>(session,checkpointPath);
 }
 void configureWindow(){
  if(!host->window)return;immersive(host->activity);const auto [w,h]=windowExtent(host->window);physicalWidth=std::max(1,w);physicalHeight=std::max(1,h);
  const double scale=std::min(1.,std::sqrt(550000./(double(physicalWidth)*physicalHeight)));const int rw=std::max(32,int(physicalWidth*scale)),rh=std::max(32,int(physicalHeight*scale));
  ANativeWindow_setBuffersGeometry(host->window,rw,rh,WINDOW_FORMAT_RGBA_8888);if(renderer)renderer->resize(rw,rh);else renderer=std::make_unique<Renderer>(rw,rh,4400);lastFrame=Clock::now();
 }
 void updateView(){engine->setView(session.view);sound.enable(session.view.sound&&focused);}
 void importState(const std::string& uri){
  const auto bytes=readDocument(host->activity,uri);Session candidate=session;candidate.restore(bytes);
  engine->stop();session=std::move(candidate);sequence=0;engine=std::make_unique<EngineService>(session,checkpointPath);engine->setActive(focused);engine->requestCheckpoint();if(renderer)renderer->clear();updateView();log("Validated portable state restored");
 }
 void exportState(){
  auto barrier=engine->barrier();if(barrier.wait_for(std::chrono::milliseconds(900))!=std::future_status::ready){log("Export timed out; no stale file was written");return;}
  Session accepted=barrier.get();engine->requestCheckpoint();const auto data=accepted.exportFile();const auto milliseconds=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();const auto name="Surface-"+std::to_string(milliseconds)+".surface";
  if(exportToDownloads(host->activity,data,name))log("Checkpoint exported to Downloads/Surface/"+name);else {std::ofstream out(std::filesystem::path(host->activity->externalDataPath?host->activity->externalDataPath:host->activity->internalDataPath)/name,std::ios::binary);out.write(reinterpret_cast<const char*>(data.data()),data.size());log(out?"Checkpoint exported to app files":"Checkpoint export failed");}
 }
 void draw(){
  if(!renderer||!host->window)return;
  if(uiWidth.load()>0&&uiHeight.load()>0&&(uiWidth.load()!=physicalWidth||uiHeight.load()!=physicalHeight))configureWindow();
  Session incoming=session;if(engine->snapshot(incoming,sequence)){session.physics=std::move(incoming.physics);session.view.generation=incoming.view.generation;session.view.inputSequence=incoming.view.inputSequence;}
  const auto now=Clock::now();const double dt=std::clamp(std::chrono::duration<double>(now-lastFrame).count(),.001,.05);lastFrame=now;
  if(session.view.observation==Observation::Cosmos){const auto projected=atlas::projectStars(catalogue.stars,session.view.yaw,session.view.pitch,session.view.zoom,renderer->width(),renderer->height());std::vector<SkyPoint> stars;stars.reserve(projected.size());for(const auto& s:projected)stars.push_back({s.x,s.y,s.mag,(s.flags&atlas::ColorPresent)?s.colorIndex:.9f,s.id});renderer->renderSky(stars);}
  else renderer->render(session.fields(),session.view,dt,!session.view.paused&&engine->heartbeatAge()<2);
  ANativeWindow_Buffer b{};if(ANativeWindow_lock(host->window,&b,nullptr)==0){const auto p=renderer->pixels();const int rows=std::min(b.height,renderer->height()),cols=std::min(b.width,renderer->width());for(int y=0;y<rows;y++)std::memcpy(static_cast<std::uint32_t*>(b.bits)+std::size_t(y)*b.stride,p.data()+std::size_t(y)*renderer->width(),std::size_t(cols)*4);ANativeWindow_unlockAndPost(host->window);}
 }
};

int32_t onInput(android_app* host,AInputEvent* event){
 auto& app=*static_cast<Application*>(host->userData);
 if(AInputEvent_getType(event)==AINPUT_EVENT_TYPE_KEY&&AKeyEvent_getAction(event)==AKEY_EVENT_ACTION_DOWN){
  const int key=AKeyEvent_getKeyCode(event);
  if(key>=AKEYCODE_1&&key<=AKEYCODE_7)app.session.view.observation=static_cast<Observation>(key-AKEYCODE_1);
  else if(key==AKEYCODE_SPACE)app.session.view.paused=!app.session.view.paused;
  else if(key==AKEYCODE_M)app.session.view.sound=!app.session.view.sound;
  else if(key==AKEYCODE_E||key==AKEYCODE_S){app.exportState();return 1;}
  else return 0;
  app.updateView();return 1;
 }
 if(AInputEvent_getType(event)!=AINPUT_EVENT_TYPE_MOTION)return 0;
 const int action=AMotionEvent_getAction(event)&AMOTION_EVENT_ACTION_MASK;
 const std::size_t count=AMotionEvent_getPointerCount(event);if(count==0||count>10)return 1;
 auto point=[&](std::size_t i){return std::pair{std::clamp(AMotionEvent_getX(event,i)/app.physicalWidth,0.f,1.f),std::clamp(AMotionEvent_getY(event,i)/app.physicalHeight,0.f,1.f)};};
 const auto [x,y]=point(0);const auto now=Clock::now();
 if(action==AMOTION_EVENT_ACTION_DOWN){
  app.gesture=true;app.gestureStart=now;app.peakPointers=1;app.moved=0;app.lastX=x;app.lastY=y;app.pinch=0;
  if(app.session.view.observation!=Observation::Cosmos){app.engine->inject({x,y,0,0,.7f});if(app.renderer)app.renderer->wake(x,y);app.sound.strike(x,y,.7f);}
 }else if(action==AMOTION_EVENT_ACTION_POINTER_DOWN){
  app.peakPointers=std::max(app.peakPointers,int(count));if(count>=2){const auto [x1,y1]=point(1);app.lastX=(x+x1)*.5f;app.lastY=(y+y1)*.5f;app.pinch=std::hypot(x-x1,y-y1);}
 }else if(action==AMOTION_EVENT_ACTION_MOVE&&app.gesture){
  if(count>=2){
   const auto [x1,y1]=point(1);const float cx=(x+x1)*.5f,cy=(y+y1)*.5f,distance=std::hypot(x-x1,y-y1),dx=cx-app.lastX,dy=cy-app.lastY;app.moved+=gestureTravel(dx,dy,app.pinch,distance);
   if(app.session.view.observation==Observation::Cosmos){app.session.view.yaw-=dx*3;app.session.view.pitch=std::clamp(app.session.view.pitch+dy*2,-1.56,1.56);if(app.pinch>.02f)app.session.view.zoom=std::clamp(app.session.view.zoom*distance/app.pinch,.5,7.);app.updateView();}
   else if(std::hypot(dx,dy)>.001f){app.engine->inject({cx,cy,dx,dy,-.5f});if(app.renderer)app.renderer->wake(cx,cy);}
   app.lastX=cx;app.lastY=cy;app.pinch=distance;
  }else if(app.peakPointers==1){
   const float dx=x-app.lastX,dy=y-app.lastY;app.moved+=std::hypot(dx,dy);
   if(app.session.view.observation==Observation::Cosmos){app.session.view.yaw-=dx*3;app.session.view.pitch=std::clamp(app.session.view.pitch+dy*2,-1.56,1.56);app.updateView();}
   else {float pressure=AMotionEvent_getPressure(event,0);if(!std::isfinite(pressure)||pressure<=0)pressure=.5f;pressure=std::clamp(pressure,.1f,1.f);if(std::hypot(dx,dy)>.001f){app.engine->inject({x,y,dx,dy,pressure});if(app.renderer)app.renderer->wake(x,y);app.sound.strike(x,y,pressure*.45f);}}
   app.lastX=x;app.lastY=y;
  }
 }else if(action==AMOTION_EVENT_ACTION_UP){
  const double held=std::chrono::duration<double>(now-app.gestureStart).count();
  if(gestureIsTap(app.moved,held)){
   if(app.peakPointers>=4)app.exportState();
   else if(app.peakPointers==3)app.session.view.paused=!app.session.view.paused;
   else if(app.peakPointers==2)app.session.nextObservation();
   else if(now-app.lastTap<std::chrono::milliseconds(300)){app.session.view.sound=!app.session.view.sound;app.lastTap=now-std::chrono::seconds(3);}
   else app.lastTap=now;
   app.updateView();
  }
  app.engine->requestCheckpoint();app.gesture=false;
 }else if(action==AMOTION_EVENT_ACTION_CANCEL){app.gesture=false;app.engine->requestCheckpoint();}
 return 1;
}
void onCommand(android_app* host,int32_t command){
 auto& app=*static_cast<Application*>(host->userData);
 try {
  switch(command){
   case APP_CMD_INIT_WINDOW:app.configureWindow();break;
   case APP_CMD_WINDOW_RESIZED:case APP_CMD_CONFIG_CHANGED:case APP_CMD_CONTENT_RECT_CHANGED:if(host->window)app.configureWindow();break;
   case APP_CMD_GAINED_FOCUS:case APP_CMD_RESUME:app.focused=true;app.engine->setActive(true);app.updateView();immersive(host->activity);break;
   case APP_CMD_LOST_FOCUS:case APP_CMD_PAUSE:app.focused=false;app.engine->setActive(false);app.engine->requestCheckpoint();app.sound.enable(false);break;
   case APP_CMD_TERM_WINDOW:app.engine->requestCheckpoint();app.renderer.reset();break;
   case APP_CMD_SAVE_STATE:app.engine->requestCheckpoint();break;
   case APP_CMD_DESTROY:app.engine->requestCheckpoint();break;
   default:break;
  }
 }catch(const std::exception& e){log(std::string("lifecycle: ")+e.what());}
}
}

extern "C" JNIEXPORT void JNICALL Java_org_surface_nativeink_SurfaceActivity_nativeDimensions(JNIEnv*,jclass,jint width,jint height){
 if(width>0&&height>0&&width<=16384&&height<=16384){uiWidth.store(width);uiHeight.store(height);}
}
extern "C" JNIEXPORT void JNICALL Java_org_surface_nativeink_SurfaceActivity_nativeOpen(JNIEnv* env,jclass,jstring value){
 if(!value||env->GetStringUTFLength(value)>8192)return;const char* uri=env->GetStringUTFChars(value,nullptr);if(!uri)return;{std::lock_guard lock(importMutex);importUri=uri;}env->ReleaseStringUTFChars(value,uri);
}

void android_main(android_app* host){
 try {
  Application application(host);host->userData=&application;host->onAppCmd=onCommand;host->onInputEvent=onInput;immersive(host->activity);
  while(!host->destroyRequested){
   int events=0;android_poll_source* source=nullptr;
   int ready=ALooper_pollOnce(application.renderer&&application.focused?0:50,nullptr,&events,reinterpret_cast<void**>(&source));
   if(ready>=0&&source)source->process(host,source);
   while(!host->destroyRequested&&(ready=ALooper_pollOnce(0,nullptr,&events,reinterpret_cast<void**>(&source)))>=0){if(source)source->process(host,source);}
   if(host->destroyRequested)break;
   std::string pending;{std::lock_guard lock(importMutex);pending.swap(importUri);}if(!pending.empty()){try{application.importState(pending);}catch(const std::exception& e){log(std::string("Import rejected; current state preserved: ")+e.what());}}
   if(application.renderer&&application.focused){const auto begin=Clock::now();try{application.draw();}catch(const std::exception& e){log(std::string("frame rejected: ")+e.what());application.session.view.paused=true;application.updateView();}const auto used=Clock::now()-begin;if(used<std::chrono::milliseconds(33))std::this_thread::sleep_for(std::chrono::milliseconds(33)-used);}
  }
  application.engine->stop();log("Native Surface stopped; committed checkpoints retained");
 }catch(const std::exception& e){log(std::string("Native startup failure: ")+e.what());ANativeActivity_finish(host->activity);}
}
