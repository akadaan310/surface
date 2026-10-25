#!/usr/bin/env python3
"""Build a native-only ARM64 APK using an existing pinned official Android toolchain."""
import argparse, hashlib, json, os, pathlib, subprocess, time, zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
def run(args,timeout=180):
    print('RUN', ' '.join(str(a) for a in args), flush=True)
    subprocess.run([str(a) for a in args],cwd=ROOT,check=True,timeout=timeout)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--toolchain',type=pathlib.Path,required=True);parser.add_argument('--keystore',type=pathlib.Path);options=parser.parse_args()
    tc=options.toolchain.resolve();ndk=tc/'android-ndk-r30';llvm=ndk/'toolchains/llvm/prebuilt/linux-x86_64';bt=tc/'android-16';platform=tc/'android-36/android.jar';out=ROOT/'build/android';out.mkdir(parents=True,exist_ok=True)
    clang=llvm/'bin/clang';cxx=llvm/'bin/clang++';glue=ndk/'sources/android/native_app_glue'
    common=['--target=aarch64-linux-android29',f'--sysroot={llvm / "sysroot"}','-O3','-fPIC','-fno-strict-aliasing','-ffunction-sections','-fdata-sections','-Wall','-Wextra']
    run([clang,*common,'-I',glue,'-c',glue/'android_native_app_glue.c','-o',out/'native_app_glue.o'])
    sources=['physics','renderer','session','checkpoint','engine_service','atlas','phantom','acoustic']
    run([cxx,*common,'-std=c++20','-Iinclude','-I',glue,'-shared','-static-libstdc++','-Wl,-z,max-page-size=16384','-Wl,--gc-sections','-Wl,--build-id=sha1','-Wl,-u,ANativeActivity_onCreate',*[ROOT/'src'/f'{s}.cpp' for s in sources],ROOT/'android/native_main.cpp',out/'native_app_glue.o','-landroid','-llog','-laaudio','-lm','-o',out/'libsurface.so'])
    run([llvm/'bin/llvm-strip','--strip-unneeded',out/'libsurface.so'])
    classes=out/'classes';classes.mkdir(exist_ok=True)
    run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-classpath',platform,'-d',classes,ROOT/'android/SurfaceActivity.java'])
    run(['java','-cp',bt/'lib/d8.jar','com.android.tools.r8.D8','--min-api','29','--lib',platform,'--output',out,*sorted(classes.rglob('*.class'))])
    unsigned=out/'surface-unsigned.apk';aligned=out/'surface-aligned.apk';apk=ROOT/'build/Surface-arm64.apk'
    run([bt/'aapt2','link','-I',platform,'--manifest',ROOT/'android/AndroidManifest.xml','--min-sdk-version','29','--target-sdk-version','36','-A',ROOT/'data','-o',unsigned])
    with zipfile.ZipFile(unsigned,'a',zipfile.ZIP_DEFLATED,6) as archive:
        archive.write(out/'libsurface.so','lib/arm64-v8a/libsurface.so')
        archive.write(out/'classes.dex','classes.dex')
    run([bt/'zipalign','-f','-p','4',unsigned,aligned])
    key=options.keystore or tc/'surface-development.keystore'
    if not key.exists():
        run(['keytool','-genkeypair','-keystore',key,'-storepass','android','-keypass','android','-alias','surface-development','-keyalg','RSA','-keysize','3072','-validity','10000','-dname','CN=Surface Development, O=Surface, C=US','-noprompt'])
    run([bt/'apksigner','sign','--ks',key,'--ks-key-alias','surface-development','--ks-pass','pass:android','--key-pass','pass:android','--out',apk,aligned])
    run([bt/'apksigner','verify','--verbose','--print-certs',apk])
    run([bt/'zipalign','-c','-v','4',apk])
    receipt={'artifact':str(apk.relative_to(ROOT)),'sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'bytes':apk.stat().st_size,'architecture':'arm64-v8a','min_android_api':29,'target_android_api':36,'ndk':'30.0.16248370','renderer':'Surface original CPU rasterizer','webview':False,'opengl':False,'network_permission':False,'signing':'development certificate; private build','verification':'compiler/link, APK signature and ZIP alignment; device execution separate','built_utc_epoch':int(time.time())}
    (ROOT/'evidence/android-build.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
