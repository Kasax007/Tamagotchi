package net.kasax.tamacraft.test;

import java.nio.file.Path;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/** The test mod on both sides: the server game tests and, with -Dtama.dump=file, the registry dump. */
@Mod("tamacraft_gametest")
public final class GameTestMod {
    private static final Logger LOG = LoggerFactory.getLogger("TamaTest");

    public GameTestMod(IEventBus modBus) {
        modBus.addListener(ServerTests::registerTests);
        modBus.addListener((net.neoforged.neoforge.registries.RegisterEvent event) -> {
            if (event.getRegistryKey().equals(net.minecraft.core.registries.Registries.TEST_FUNCTION)) {
                ServerTests.registerFunctions();
            }
        });
        String dump = System.getProperty("tama.dump");
        if (dump != null) {
            NeoForge.EVENT_BUS.addListener((ServerStartedEvent event) -> {
                try {
                    RegistryDump.write(event.getServer(), Path.of(dump));
                    LOG.info("[TamaTest] registry dump written to {}", dump);
                } catch (Exception e) {
                    LOG.error("[TamaTest] registry dump failed", e);
                }
                event.getServer().halt(false);
            });
        }
    }
}
