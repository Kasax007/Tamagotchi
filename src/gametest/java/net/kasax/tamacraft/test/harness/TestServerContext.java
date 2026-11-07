package net.kasax.tamacraft.test.harness;

import java.util.function.Consumer;
import net.minecraft.server.MinecraftServer;

/** The integrated server of a test world: commands and code run on the server thread, the test waits for them. */
public final class TestServerContext {
    private final MinecraftServer server;

    TestServerContext(MinecraftServer server) {
        this.server = server;
    }

    public void runCommand(String command) {
        runOnServer(s -> s.getCommands().performPrefixedCommand(s.createCommandSourceStack().withSuppressedOutput(), command));
    }

    /** Code that runs at the end of every server tick until it is set to null (one at a time). */
    public void onServerTick(Consumer<MinecraftServer> action) {
        TestRunner.serverTick = action;
    }

    public void runOnServer(Consumer<MinecraftServer> action) {
        this.server.submit(() -> action.accept(this.server)).join();
    }
}
