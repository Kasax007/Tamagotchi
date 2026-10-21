package net.kasax.tamagotchi.client.particle;

import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.fabricmc.fabric.api.client.particle.v1.ParticleProviderRegistry;
import net.kasax.tamagotchi.registry.ModParticles;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.Particle;
import net.minecraft.client.particle.ParticleProvider;
import net.minecraft.client.particle.SingleQuadParticle;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;

/** Client particle behaviours for the mod's particle types. */
@Environment(EnvType.CLIENT)
public final class PetParticles {
    private PetParticles() {
    }

    public static void register() {
        ParticleProviderRegistry r = ParticleProviderRegistry.getInstance();
        r.register(ModParticles.ZZZ, sprites -> provider(sprites, Kind.ZZZ));
        r.register(ModParticles.SPARKLE, sprites -> provider(sprites, Kind.SPARKLE));
        r.register(ModParticles.SWEAT, sprites -> provider(sprites, Kind.SWEAT));
        r.register(ModParticles.STINK, sprites -> provider(sprites, Kind.STINK));
        r.register(ModParticles.LASER_DOT, sprites -> provider(sprites, Kind.LASER));
        r.register(ModParticles.LEAF, sprites -> provider(sprites, Kind.LEAF));
        r.register(ModParticles.SONAR, sprites -> provider(sprites, Kind.SONAR));
        for (SimpleParticleType t : new SimpleParticleType[]{ModParticles.EMOTE_HUNGRY, ModParticles.EMOTE_SLEEPY,
                ModParticles.EMOTE_DIRTY, ModParticles.EMOTE_BORED, ModParticles.EMOTE_SAD, ModParticles.EMOTE_LOVE}) {
            r.register(t, sprites -> provider(sprites, Kind.EMOTE));
        }
    }

    private static ParticleProvider<SimpleParticleType> provider(SpriteSet sprites, Kind kind) {
        return (SimpleParticleType options, ClientLevel level, double x, double y, double z, double xa, double ya, double za,
                RandomSource random) -> new PetParticle(level, x, y, z, xa, ya, za, sprites, kind, random);
    }

    enum Kind { ZZZ, SPARKLE, SWEAT, STINK, LASER, LEAF, SONAR, EMOTE }

    static final class PetParticle extends SingleQuadParticle {
        private final SpriteSet sprites;
        private final Kind kind;
        private final float baseSize;
        private final float phase;

        PetParticle(ClientLevel level, double x, double y, double z, double xa, double ya, double za, SpriteSet sprites, Kind kind,
                    RandomSource random) {
            super(level, x, y, z, sprites.get(random));
            this.sprites = sprites;
            this.kind = kind;
            this.phase = random.nextFloat() * Mth.TWO_PI;
            this.hasPhysics = false;
            this.gravity = 0;
            this.xd = xa;
            this.yd = ya;
            this.zd = za;
            switch (kind) {
                case ZZZ -> {
                    this.lifetime = 40;
                    this.quadSize = 0.14F;
                    this.yd = 0.02;
                }
                case SPARKLE -> {
                    this.lifetime = 14 + random.nextInt(8);
                    this.quadSize = 0.09F + random.nextFloat() * 0.05F;
                    this.yd = 0.01;
                    setSpriteFromAge(sprites);
                }
                case SWEAT -> {
                    this.lifetime = 18;
                    this.quadSize = 0.09F;
                    this.xd = (random.nextFloat() - 0.5F) * 0.12;
                    this.yd = 0.1;
                    this.zd = (random.nextFloat() - 0.5F) * 0.12;
                    this.gravity = 0.6F;
                    this.hasPhysics = true;
                }
                case STINK -> {
                    this.lifetime = 30;
                    this.quadSize = 0.12F;
                    this.yd = 0.015;
                }
                case LASER -> {
                    this.lifetime = 3;
                    this.quadSize = 0.09F;
                    this.xd = this.yd = this.zd = 0;
                }
                case LEAF -> {
                    this.lifetime = 40 + random.nextInt(20);
                    this.quadSize = 0.08F;
                    this.gravity = 0.06F;
                    this.hasPhysics = true;
                    this.roll = random.nextFloat() * Mth.TWO_PI;
                }
                case SONAR -> {
                    this.lifetime = 22;
                    this.quadSize = 0.3F;
                    this.xd = this.yd = this.zd = 0;
                }
                case EMOTE -> {
                    this.lifetime = 36;
                    this.quadSize = 0.22F;
                    this.xd = this.zd = 0;
                    this.yd = 0.012;
                }
            }
            this.baseSize = this.quadSize;
        }

        @Override
        public void tick() {
            super.tick();
            float t = this.age / (float) this.lifetime;
            switch (this.kind) {
                case ZZZ -> {
                    this.xd = Math.sin(this.age * 0.25 + this.phase) * 0.01;
                    this.quadSize = this.baseSize * (0.6F + t * 0.8F);
                    this.alpha = t > 0.7F ? 1F - (t - 0.7F) / 0.3F : 1F;
                }
                case SPARKLE -> setSpriteFromAge(this.sprites);
                case STINK -> {
                    this.xd = Math.sin(this.age * 0.4 + this.phase) * 0.015;
                    this.alpha = 1F - t;
                }
                case LEAF -> {
                    this.oRoll = this.roll;
                    this.roll += 0.08F;
                    this.xd += Math.sin(this.age * 0.2 + this.phase) * 0.004;
                }
                case SONAR -> {
                    this.quadSize = this.baseSize + t * 2.8F;
                    this.alpha = 1F - t;
                }
                case EMOTE -> {
                    // pop in, hover, fade out
                    float pop = t < 0.15F ? Mth.sin(t / 0.15F * Mth.HALF_PI) * 1.15F : (t < 0.25F ? 1.15F - (t - 0.15F) * 1.5F : 1F);
                    this.quadSize = this.baseSize * pop;
                    this.yd = t < 0.2F ? 0.02 : 0.002;
                    this.alpha = t > 0.8F ? 1F - (t - 0.8F) / 0.2F : 1F;
                }
                default -> {
                }
            }
        }

        @Override
        protected int getLightCoords(float a) {
            return this.kind == Kind.SPARKLE || this.kind == Kind.LASER || this.kind == Kind.SONAR || this.kind == Kind.EMOTE
                    ? 0xF000F0 : super.getLightCoords(a);
        }

        @Override
        public SingleQuadParticle.Layer getLayer() {
            return SingleQuadParticle.Layer.TRANSLUCENT;
        }
    }
}
