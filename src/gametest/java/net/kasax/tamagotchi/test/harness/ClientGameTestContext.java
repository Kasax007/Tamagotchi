package net.kasax.tamagotchi.test.harness;

import java.io.File;
import java.util.concurrent.CompletableFuture;
import java.util.function.Consumer;
import java.util.function.Function;
import net.kasax.tamagotchi.test.mixin.MouseHandlerAccessor;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * A small stand-in for Fabric's client game-test context, which 1.21.1 does not have yet. The test runs on its own
 * thread; {@link #waitTicks} lets the game run, {@link #runOnClient} does something on the client thread and waits
 * for it. The method names are the ones of the Fabric API, so the tests read like the 26.x ones.
 */
public final class ClientGameTestContext {
    private static final Logger LOG = LoggerFactory.getLogger("TamaTest");
    private final Minecraft mc;
    private final TestInput input = new TestInput();
    private final Object tickLock = new Object();
    private volatile long ticks;

    ClientGameTestContext(Minecraft mc) {
        this.mc = mc;
    }

    /** Called by the runner at the end of every client tick. */
    void onTick() {
        synchronized (this.tickLock) {
            this.ticks++;
            this.tickLock.notifyAll();
        }
    }

    public Minecraft client() {
        return this.mc;
    }

    public void waitTicks(int n) {
        long until = this.ticks + n;
        synchronized (this.tickLock) {
            while (this.ticks < until) {
                try {
                    this.tickLock.wait(1000);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    throw new RuntimeException(e);
                }
            }
        }
    }

    public void waitTick() {
        waitTicks(1);
    }

    /** Waits (up to {@code maxTicks}) until {@code done} is true on the client; false on timeout. */
    public boolean waitFor(Function<Minecraft, Boolean> done, int maxTicks) {
        for (int i = 0; i < maxTicks; i++) {
            if (computeOnClient(done)) {
                return true;
            }
            waitTick();
        }
        return false;
    }

    public void runOnClient(Consumer<Minecraft> action) {
        computeOnClient(mc -> {
            action.accept(mc);
            return null;
        });
    }

    public <T> T computeOnClient(Function<Minecraft, T> action) {
        CompletableFuture<T> f = this.mc.submit(() -> action.apply(this.mc));
        return f.join();
    }

    public TestInput getInput() {
        return this.input;
    }

    public TestWorldBuilder worldBuilder() {
        return new TestWorldBuilder(this);
    }

    /** A screenshot of the last frame, into run/screenshots/&lt;name&gt;.png. */
    public void takeScreenshot(TestScreenshotOptions options) {
        waitTick();
        String name = options.name() + ".png";
        runOnClient(mc -> Screenshot.grab(mc.gameDirectory, name, mc.getMainRenderTarget(), msg -> { }));
        LOG.info("[TamaTest] screenshot {}", new File(this.mc.gameDirectory, "screenshots/" + name));
    }

    /** Real input through the game's own mouse and keyboard handlers (GLFW numbering on 1.21.1). */
    public final class TestInput {
        public void resizeWindow(int width, int height) {
            runOnClient(mc -> org.lwjgl.glfw.GLFW.glfwSetWindowSize(mc.getWindow().getWindow(), width, height));
            waitTicks(5);
        }

        public void setCursorPos(double x, double y) {
            runOnClient(mc -> ((MouseHandlerAccessor) mc.mouseHandler).tamatest$onMove(mc.getWindow().getWindow(), x, y));
        }

        public void pressMouse(int button) {
            runOnClient(mc -> ((MouseHandlerAccessor) mc.mouseHandler).tamatest$onPress(mc.getWindow().getWindow(), button,
                    org.lwjgl.glfw.GLFW.GLFW_PRESS, 0));
            waitTick();
            runOnClient(mc -> ((MouseHandlerAccessor) mc.mouseHandler).tamatest$onPress(mc.getWindow().getWindow(), button,
                    org.lwjgl.glfw.GLFW.GLFW_RELEASE, 0));
        }

        public void pressKey(int key) {
            runOnClient(mc -> mc.keyboardHandler.keyPress(mc.getWindow().getWindow(), key, 0, org.lwjgl.glfw.GLFW.GLFW_PRESS, 0));
            runOnClient(mc -> mc.keyboardHandler.keyPress(mc.getWindow().getWindow(), key, 0, org.lwjgl.glfw.GLFW.GLFW_RELEASE, 0));
        }

        public void typeChars(String text) {
            text.codePoints().forEach(c -> runOnClient(mc ->
                    ((net.kasax.tamagotchi.test.mixin.KeyboardHandlerAccessor) mc.keyboardHandler).tamatest$charTyped(mc.getWindow().getWindow(), c, 0)));
        }
    }
}
