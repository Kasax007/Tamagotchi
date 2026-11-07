package net.kasax.tamacraft.test.harness;

import java.util.OptionalLong;
import net.minecraft.client.gui.screens.GenericMessageScreen;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.Difficulty;
import net.minecraft.world.level.GameRules;
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

    public TestSingleplayerContext create() {
        String name = "tamatest_" + (++counter);
        boolean flat = this.consistent;
        String seedText = this.seed;
        this.ctx.runOnClient(mc -> {
            GameRules rules = new GameRules();
            if (flat) {
                rules.getRule(GameRules.RULE_DAYLIGHT).set(false, null);
                rules.getRule(GameRules.RULE_WEATHER_CYCLE).set(false, null);
                rules.getRule(GameRules.RULE_DOMOBSPAWNING).set(false, null);
            }
            LevelSettings settings = new LevelSettings(name, GameType.CREATIVE, false, Difficulty.NORMAL, true, rules,
                    WorldDataConfiguration.DEFAULT);
            OptionalLong parsed = WorldOptions.parseSeed(seedText);
            WorldOptions options = new WorldOptions(parsed.orElse(flat ? 1L : WorldOptions.randomSeed()), true, false);
            ResourceKey<WorldPreset> preset = flat ? WorldPresets.FLAT : WorldPresets.NORMAL;
            mc.createWorldOpenFlows().createFreshLevel(name, settings, options,
                    access -> access.registryOrThrow(Registries.WORLD_PRESET).getHolderOrThrow(preset).value().createWorldDimensions(),
                    new TitleScreen());
        });
        boolean in = this.ctx.waitFor(mc -> mc.level != null && mc.player != null && mc.screen == null && mc.getSingleplayerServer() != null,
                20 * 120);
        if (!in) {
            throw new IllegalStateException("the test world " + name + " did not load");
        }
        this.ctx.waitTicks(20);
        return new TestSingleplayerContext(this.ctx, new TestServerContext(this.ctx.computeOnClient(mc -> mc.getSingleplayerServer())));
    }

    /** The open test world; closing it leaves to the title screen. */
    public static final class TestSingleplayerContext implements AutoCloseable {
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
                if (mc.level != null) {
                    mc.level.disconnect();
                }
                mc.disconnect(new GenericMessageScreen(Component.literal("Saving")));
                mc.setScreen(new TitleScreen());
            });
            this.ctx.waitFor(mc -> mc.getSingleplayerServer() == null && mc.level == null, 20 * 60);
            this.ctx.waitTicks(10);
        }
    }
}
