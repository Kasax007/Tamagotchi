package net.kasax.tamacraft.test.harness;

import net.minecraft.client.gui.screens.TitleScreen;

/** The open test world; closing it leaves to the title screen. */
public final class TestSingleplayerContext implements AutoCloseable {
    private final ClientGameTestContext ctx;
    private final TestServerContext server;

    TestSingleplayerContext(ClientGameTestContext ctx, TestServerContext server) {
        this.ctx = ctx;
        this.server = server;
    }

    public TestServerContext getServer() {
        return this.server;
    }

    @Override
    public void close() {
        this.ctx.runOnClient(mc -> {
            mc.disconnectWithSavingScreen();
            mc.gui.setScreen(new TitleScreen());
        });
        this.ctx.waitFor(mc -> mc.getSingleplayerServer() == null && mc.level == null, 20 * 60);
        this.ctx.waitTicks(10);
    }
}
