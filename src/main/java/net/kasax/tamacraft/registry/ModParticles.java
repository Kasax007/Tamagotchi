package net.kasax.tamacraft.registry;

import net.kasax.tamacraft.Tamacraft;
import net.minecraft.core.Registry;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.core.registries.BuiltInRegistries;

/** Custom particles: sleep Zs, sparkles, emote bubbles and the like. */
public final class ModParticles {
    public static final SimpleParticleType ZZZ = simple(false);
    public static final SimpleParticleType HEART = simple(false);
    public static final SimpleParticleType SPARKLE = simple(false);
    public static final SimpleParticleType SWEAT = simple(false);
    public static final SimpleParticleType STINK = simple(false);
    public static final SimpleParticleType LASER_DOT = simple(true);
    public static final SimpleParticleType LEAF = simple(false);
    public static final SimpleParticleType SONAR = simple(true);
    public static final SimpleParticleType EMOTE_HUNGRY = simple(false);
    public static final SimpleParticleType EMOTE_SLEEPY = simple(false);
    public static final SimpleParticleType EMOTE_DIRTY = simple(false);
    public static final SimpleParticleType EMOTE_BORED = simple(false);
    public static final SimpleParticleType EMOTE_SAD = simple(false);
    public static final SimpleParticleType EMOTE_LOVE = simple(false);

    private ModParticles() {
    }

    private static SimpleParticleType simple(boolean alwaysShow) {
        return new SimpleParticleType(alwaysShow) {
        };
    }

    private static void reg(String name, SimpleParticleType type) {
        Registry.register(BuiltInRegistries.PARTICLE_TYPE, Tamacraft.id(name), type);
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
