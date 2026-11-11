package net.kasax.tamacraft.test.harness;

import java.util.OptionalLong;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.Difficulty;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.LevelSettings;
import net.minecraft.world.level.WorldDataConfiguration;
import net.minecraft.world.level.levelgen.WorldOptions;
import net.minecraft.world.level.levelgen.presets.WorldPreset;
import net.minecraft.world.level.levelgen.presets.WorldPresets;

/**
 * Creates a singleplayer world like Fabric's test world builder: by default a flat creative world with fixed settings
 * (no daylight or weather cycle, no mob spawning); {@code setUseConsistentSettings(false)} gives a normal world.
 */
public final class TestWorldBuilder {
    private static int counter;
    private final ClientGameTestContext ctx;
    private boolean consistent = true;
    private String seed = "";

    TestWorldBuilder(ClientGameTestContext ctx) {
        this.ctx = ctx;
    }

    public TestWorldBuilder setUseConsistentSettings(boolean consistent) {
        this.consistent = consistent;
        return this;
    }

    public TestWorldBuilder setSeed(String seed) {
        this.seed = seed;
        return this;
    }

    /** The settings the tests change (Fabric: the world creation screen's state). */
    public final class Settings {
        public void setSeed(String seed) {
            TestWorldBuilder.this.seed = seed;
        }
    }

    public TestWorldBuilder adjustSettings(java.util.function.Consumer<Settings> adjust) {
        adjust.accept(new Settings());
        return this;
    }

    public TestSingleplayerContext create() {
        String name = "tamatest_" + (++counter);
        boolean flat = this.consistent;
        String seedText = this.seed;
        this.ctx.runOnClient(mc -> {
            LevelSettings settings = new LevelSettings(name, GameType.CREATIVE,
                    new LevelSettings.DifficultySettings(Difficulty.NORMAL, false, false), true, WorldDataConfiguration.DEFAULT);
            OptionalLong parsed = WorldOptions.parseSeed(seedText);
            WorldOptions options = new WorldOptions(parsed.orElse(flat ? 1L : WorldOptions.randomSeed()), !flat, false);
            ResourceKey<WorldPreset> preset = flat ? WorldPresets.FLAT : WorldPresets.NORMAL;
            mc.createWorldOpenFlows().createFreshLevel(name, settings, options,
                    access -> access.lookupOrThrow(Registries.WORLD_PRESET).getOrThrow(preset).value().createWorldDimensions(),
                    new TitleScreen());
        });
        boolean in = this.ctx.waitFor(mc -> mc.level != null && mc.player != null && mc.gui.screen() == null
                && mc.getSingleplayerServer() != null, 20 * 120);
        if (!in) {
            throw new IllegalStateException("the test world " + name + " did not load");
        }
        TestServerContext server = new TestServerContext(this.ctx.computeOnClient(mc -> mc.getSingleplayerServer()));
        if (flat) {
            server.runCommand("gamerule advance_time false");
            server.runCommand("gamerule advance_weather false");
            server.runCommand("gamerule spawn_mobs false");
            // 26.3 creates the world before the rules can be set: the slimes of the first ticks go again
            server.runCommand("kill @e[type=!minecraft:player]");
        }
        this.ctx.waitTicks(20);
        return new TestSingleplayerContext(this.ctx, server);
    }
}
