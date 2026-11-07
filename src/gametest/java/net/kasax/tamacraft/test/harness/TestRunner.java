package net.kasax.tamacraft.test.harness;

import java.util.List;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.kasax.tamacraft.test.BlockGallery;
import net.kasax.tamacraft.test.PetGallery;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.TitleScreen;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Runs the client tests once the title screen is up (only with -Dtama.selftest, which the clientGameTest run sets),
 * then closes the game. Results are the "[TamaTest] PASS / FAIL" lines in the log.
 */
public final class TestRunner implements ClientModInitializer {
    private static final Logger LOG = LoggerFactory.getLogger("TamaTest");
    /** See {@link TestServerContext#onServerTick}. */
    static volatile java.util.function.Consumer<net.minecraft.server.MinecraftServer> serverTick;
    private ClientGameTestContext ctx;
    private boolean started;

    @Override
    public void onInitializeClient() {
        if (System.getProperty("tama.selftest") == null) {
            return;
        }
        net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_SERVER_TICK.register(server -> {
            var hook = serverTick;
            if (hook != null) {
                hook.accept(server);
            }
        });
        ClientTickEvents.END_CLIENT_TICK.register(mc -> {
            if (this.ctx != null) {
                this.ctx.onTick();
            }
            if (!this.started && mc.screen != null && mc.getOverlay() == null) {
                // the first start shows the accessibility onboarding screen instead of the title screen
                this.started = true;
                mc.options.onboardAccessibility = false;
                mc.options.tutorialStep = net.minecraft.client.tutorial.TutorialSteps.NONE;
                mc.getTutorial().setStep(net.minecraft.client.tutorial.TutorialSteps.NONE);
                mc.options.save();
                if (!(mc.screen instanceof TitleScreen)) {
                    mc.setScreen(new TitleScreen());
                }
                this.ctx = new ClientGameTestContext(mc);
                Thread t = new Thread(() -> run(mc), "TamaTest");
                t.setDaemon(true);
                t.start();
            }
        });
    }

    private void run(Minecraft mc) {
        int code = 0;
        try {
            this.ctx.waitTicks(20);
            for (FabricClientGameTest test : List.of(new PetGallery(), new BlockGallery())) {
                LOG.info("[TamaTest] running {}", test.getClass().getSimpleName());
                test.runTest(this.ctx);
            }
            LOG.info("[TamaTest] all tests finished");
        } catch (Throwable e) {
            LOG.error("[TamaTest] FAIL the test run crashed", e);
            code = 1;
        }
        int exit = code;
        mc.execute(() -> {
            LOG.info("[TamaTest] stopping the client (exit {})", exit);
            mc.stop();
        });
    }
}
