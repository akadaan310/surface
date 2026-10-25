package org.surface.nativeink;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;

/** Executes the actual Activity class' static JNI bridge, without constructing Android UI. */
public final class StartupProbe {
    private static native int observe(int field);

    private static void expect(int field, int expected) {
        int actual = observe(field);
        if (actual != expected) {
            throw new AssertionError("field " + field + ": expected " + expected + ", got " + actual);
        }
    }

    public static void main(String[] args) throws Exception {
        Class<?> activity = Class.forName("org.surface.nativeink.SurfaceActivity");
        System.out.println("PROBE actual SurfaceActivity class initialized");
        Method dimensions = activity.getDeclaredMethod("nativeDimensions", int.class, int.class);
        Method open = activity.getDeclaredMethod("nativeOpen", String.class);
        dimensions.setAccessible(true);
        open.setAccessible(true);
        try {
            dimensions.invoke(null, 320, 480);
            expect(0, 1);
            expect(1, 320);
            expect(2, 480);
            expect(3, 0);
            System.out.println("PROBE nativeDimensions resolved; first integer arguments exact");

            open.invoke(null, "content://surface-startup-regression");
            expect(3, 1);
            expect(4, 1);
            System.out.println("PROBE nativeOpen resolved; one non-null string reference received");

            dimensions.invoke(null, 1080, 2400);
            expect(0, 2);
            expect(1, 1080);
            expect(2, 2400);
            expect(3, 1);
            expect(4, 1);
            System.out.println("{\"status\":\"PASS\",\"dimension_calls\":2,\"open_calls\":1,\"width\":1080,\"height\":2400,\"nonnull_string_calls\":1}");
        } catch (InvocationTargetException failure) {
            Throwable cause = failure.getCause();
            cause.printStackTrace(System.err);
            System.exit(cause instanceof UnsatisfiedLinkError ? 42 : 43);
        }
    }
}
