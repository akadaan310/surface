#include <cstdint>

// The build host has a JRE with javac's compiler module, but no installed JNI
// headers. This Linux host fixture never dereferences JNI environment/object
// pointers. These opaque pointer declarations and signed 32-bit jint preserve
// the JNI ABI for the void/int methods below. No JNIEnv function table is used.
struct JNIEnv_;
struct _jobject;
struct _jclass;
struct _jstring;
using JNIEnv = JNIEnv_;
using jclass = _jclass*;
using jstring = _jstring*;
using jint = std::int32_t;
static_assert(sizeof(jint) == 4);
#define JNIEXPORT __attribute__((visibility("default")))
#define JNICALL

namespace {
jint dimensionCalls = 0;
jint width = 0;
jint height = 0;
jint openCalls = 0;
jint nonnullStringCalls = 0;
}

extern "C" JNIEXPORT void JNICALL
Java_org_surface_nativeink_SurfaceActivity_nativeDimensions(JNIEnv*, jclass, jint w, jint h) {
    ++dimensionCalls;
    width = w;
    height = h;
}

extern "C" JNIEXPORT void JNICALL
Java_org_surface_nativeink_SurfaceActivity_nativeOpen(JNIEnv*, jclass, jstring uri) {
    ++openCalls;
    if (uri != nullptr) ++nonnullStringCalls;
}

extern "C" JNIEXPORT jint JNICALL
Java_org_surface_nativeink_StartupProbe_observe(JNIEnv*, jclass, jint field) {
    switch (field) {
        case 0: return dimensionCalls;
        case 1: return width;
        case 2: return height;
        case 3: return openCalls;
        case 4: return nonnullStringCalls;
        default: return -1;
    }
}
