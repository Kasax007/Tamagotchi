package net.kasax.tamagotchi.registry;

import net.fabricmc.fabric.api.particle.v1.FabricParticleTypes;
import net.kasax.tamagotchi.Tamagotchi;
import net.minecraft.core.Registry;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.core.registries.BuiltInRegistries;

/** Custom particles: sleep Zs, sparkles, emote bubbles and the like. */
public final class ModParticles {
    public static final SimpleParticleType ZZZ = FabricParticleTypes.simple();
    public static final SimpleParticleType HEART = FabricParticleTypes.simple();
    public static final SimpleParticleType SPARKLE = FabricParticleTypes.simple();
    public static final SimpleParticleType SWEAT = FabricParticleTypes.simple();
    public static final SimpleParticleType STINK = FabricParticleTypes.simple();
    public static final SimpleParticleType LASER_DOT = FabricParticleTypes.simple(true);
    public static final SimpleParticleType LEAF = FabricParticleTypes.simple();
    public static final SimpleParticleType SONAR = FabricParticleTypes.simple(true);
    public static final SimpleParticleType EMOTE_HUNGRY = FabricParticleTypes.simple();
    public static final SimpleParticleType EMOTE_SLEEPY = FabricParticleTypes.simple();
    public static final SimpleParticleType EMOTE_DIRTY = FabricParticleTypes.simple();
    public static final SimpleParticleType EMOTE_BORED = FabricParticleTypes.simple();
    public static final SimpleParticleType EMOTE_SAD = FabricParticleTypes.simple();
    public static final SimpleParticleType EMOTE_LOVE = FabricParticleTypes.simple();

    private ModParticles() {
    }

    private static void reg(String name, SimpleParticleType type) {
        Registry.register(BuiltInRegistries.PARTICLE_TYPE, Tamagotchi.id(name), type);
    }

    public static void initialize() {
        reg("zzz", ZZZ);
        reg("heart", HEART);
        reg("sparkle", SPARKLE);
        reg("sweat", SWEAT);
        reg("stink", STINK);
        reg("laser_dot", LASER_DOT);
        reg("leaf", LEAF);
        reg("sonar", SONAR);
        reg("emote_hungry", EMOTE_HUNGRY);
        reg("emote_sleepy", EMOTE_SLEEPY);
        reg("emote_dirty", EMOTE_DIRTY);
        reg("emote_bored", EMOTE_BORED);
        reg("emote_sad", EMOTE_SAD);
        reg("emote_love", EMOTE_LOVE);
    }
}
