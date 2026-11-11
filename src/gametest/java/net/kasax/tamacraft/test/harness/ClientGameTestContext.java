package net.kasax.tamacraft.test.harness;

import java.io.File;
import java.util.concurrent.CompletableFuture;
import java.util.function.Consumer;
import java.util.function.Function;
import com.mojang.blaze3d.platform.InputConstants;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.input.CharacterEvent;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.MouseButtonInfo;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * A small stand-in for Fabric's client game-test context (NeoForge has none). The test runs on its own thread;
 * {@link #waitTicks} lets the game run, {@link #runOnClient} does something on the client thread and waits for it.
 * The method names are the ones of the Fabric API, so the tests are the same as the Fabric build's.
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
        runOnClient(mc -> mc.gui.toastManager().clear());   // like Fabric's test client: no toasts in the pictures
        waitTick();
        String name = options.name() + ".png";
        runOnClient(mc -> Screenshot.grab(mc.gameDirectory, name, mc.gameRenderer.mainRenderTarget(), 1, msg -> { }));
        waitTicks(2);
        LOG.info("[TamaTest] screenshot {}", new File(this.mc.gameDirectory, "screenshots/" + name));
    }

    /** Real input through the game's own mouse and keyboard handlers (26.3 numbering: SDL, left button = 1). */
    public final class TestInput {
        public void resizeWindow(int width, int height) {
            runOnClient(mc -> mc.getWindow().setWindowed(width, height));
            waitTicks(5);
        }

        public void setCursorPos(double x, double y) {
            runOnClient(mc -> {
                long handle = mc.getWindow().handle();
                mc.mouseHandler.onMove(handle, x, y, 0, 0);
                mc.mouseHandler.onMove(handle, x, y, 0, 0);   // the first move after a while only sets the position
            });
        }

        public void pressMouse(int button) {
            runOnClient(mc -> mc.mouseHandler.onButton(mc.getWindow().handle(), new MouseButtonInfo(button, 0), InputConstants.PRESS));
            waitTick();
            runOnClient(mc -> mc.mouseHandler.onButton(mc.getWindow().handle(), new MouseButtonInfo(button, 0), InputConstants.RELEASE));
        }

        public void pressKey(int key) {
            runOnClient(mc -> mc.keyboardHandler.keyPress(mc.getWindow().handle(), InputConstants.PRESS, new KeyEvent(key, 0, 0)));
            runOnClient(mc -> mc.keyboardHandler.keyPress(mc.getWindow().handle(), InputConstants.RELEASE, new KeyEvent(key, 0, 0)));
        }

        public void typeChars(String text) {
            text.codePoints().forEach(c -> runOnClient(mc -> mc.keyboardHandler.charTyped(mc.getWindow().handle(), new CharacterEvent(c))));
        }
    }
}
