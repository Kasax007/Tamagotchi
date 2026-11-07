package net.kasax.tamagotchi.test.harness;

/** Screenshot name (the Fabric API's options, reduced to what the tests use). */
public record TestScreenshotOptions(String name) {
    public static TestScreenshotOptions of(String name) {
        return new TestScreenshotOptions(name);
    }

    public TestScreenshotOptions disableCounterPrefix() {
        return this;
    }
}
