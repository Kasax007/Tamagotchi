package net.kasax.tamacraft.test.harness;

import java.util.List;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
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
@Mod(value = "tamacraft_gametest", dist = Dist.CLIENT)
public final class TestRunner {
    private static final Logger LOG = LoggerFactory.getLogger("TamaTest");
    /** See {@link TestServerContext#onServerTick}. */
    static volatile java.util.function.Consumer<net.minecraft.server.MinecraftServer> serverTick;
    private ClientGameTestContext ctx;
    private boolean started;

    public TestRunner() {
        if (System.getProperty("tama.selftest") == null) {
            return;
        }
        NeoForge.EVENT_BUS.addListener((ServerTickEvent.Post event) -> {
            var hook = serverTick;
            if (hook != null) {
                hook.accept(event.getServer());
            }
        });
        NeoForge.EVENT_BUS.addListener((ClientTickEvent.Post event) -> {
            Minecraft mc = Minecraft.getInstance();
            if (this.ctx != null) {
                this.ctx.onTick();
            }
            if (!this.started && mc.gui.screen() != null && mc.gui.overlay() == null) {
                // the first start shows the accessibility onboarding screen instead of the title screen
                this.started = true;
                mc.options.onboardAccessibility = false;
                mc.options.tutorialStep = net.minecraft.client.tutorial.TutorialSteps.NONE;
                mc.getTutorial().setStep(net.minecraft.client.tutorial.TutorialSteps.NONE);
                mc.options.save();
                if (!(mc.gui.screen() instanceof TitleScreen)) {
                    mc.gui.setScreen(new TitleScreen());
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
