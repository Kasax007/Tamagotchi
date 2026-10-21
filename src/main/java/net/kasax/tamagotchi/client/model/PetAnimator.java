package net.kasax.tamagotchi.client.model;

import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.kasax.tamagotchi.client.render.PetRenderState;
import net.kasax.tamagotchi.pet.PetAction;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.kasax.tamagotchi.pet.PetSpecies.Gait;
import net.kasax.tamagotchi.pet.TamaPet;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;
import org.jspecify.annotations.Nullable;

/**
 * Procedural animation for every pet, layered: look → idle → gait → poses → one-shot actions.
 * Model space: Y points down, the pet faces -Z, positive xRot tips a head's nose down, swings a
 * leg backwards and lifts a tail.
 */
@Environment(EnvType.CLIENT)
public final class PetAnimator {
    private static final float PI = Mth.PI;

    private PetAnimator() {
    }

    // ------------------------------------------------------------------ helpers

    static float env(float t) {
        return Mth.sin(t * PI);
    }

    /** Parabolic hop between a and b (0..1 of the clip), peak 1. */
    static float hop(float t, float a, float b) {
        if (t < a || t > b) {
            return 0;
        }
        float u = (t - a) / (b - a);
        return 4 * u * (1 - u);
    }

    /** 0 → 1 ramp over [a, b]. */
    static float ramp(float t, float a, float b) {
        return Mth.clamp((t - a) / (b - a), 0, 1);
    }

    /** Occasional twitch: mostly 0 with short spikes. */
    static float twitch(float time, float speed, float phase) {
        float s = Mth.sin(time * speed + phase);
        return s > 0.96F ? (s - 0.96F) / 0.04F : 0;
    }

    static void rot(@Nullable ModelPart p, float x, float y, float z) {
        if (p != null) {
            p.xRot += x;
            p.yRot += y;
            p.zRot += z;
        }
    }

    static void off(@Nullable ModelPart p, float x, float y, float z) {
        if (p != null) {
            p.x += x;
            p.y += y;
            p.z += z;
        }
    }

    static void setX(@Nullable ModelPart p, float xRot) {
        if (p != null) {
            p.xRot = xRot;
        }
    }

    static boolean quadruped(PetModel m) {
        return m.legFL != null && m.legBL != null;
    }

    /** Pets whose face is painted on the body: look by turning the body, not a head bone. */
    static boolean bodyLooks(PetSpecies s) {
        return s == PetSpecies.SCULK_WISP || s == PetSpecies.PEBBLE_GOLEM || s == PetSpecies.MIMIC;
    }

    // ------------------------------------------------------------------ entry point

    public static void animate(PetModel m, PetRenderState s) {
        ModelPart root = m.rootPart();
        float t = s.ageInTicks;
        float pos = s.walkAnimationPos;
        float spd = Math.min(1F, s.walkAnimationSpeed);
        PetSpecies sp = m.species;
        boolean sleeping = s.has(TamaPet.F_SLEEPING);
        boolean running = s.has(TamaPet.F_RUNNING);
        boolean bathing = s.has(TamaPet.F_BATHING);

        if (m.backpack != null) {
            m.backpack.visible = s.has(TamaPet.F_BACKPACK);
        }
        if (m.tongue != null && sp == PetSpecies.HEX_TOAD) {
            m.tongue.visible = false;
        }

        look(m, s, sleeping);
        idle(m, s, t, sleeping);

        if (running) {
            gait(m, s, t * 1.5F, 1F, t);
        } else if (!sleeping && !s.sitting && !bathing && !s.has(TamaPet.F_SLIDING)) {
            gait(m, s, pos, spd, t);
        }

        if (sleeping) {
            sleepPose(m, s, t);
        } else if (s.sitting || s.has(TamaPet.F_BEGGING) || s.has(TamaPet.F_WARMING)) {
            sitPose(m, s);
        }
        if (s.has(TamaPet.F_SLIDING)) {
            slide(m, s, t);
        }
        if (bathing) {
            off(m.body, 0, 2.5F, 0);
            rot(m.body, 0, 0, Mth.sin(t * 0.9F) * 0.15F);
            rot(m.head, -0.3F, 0, Mth.sin(t * 0.9F + 1) * 0.2F);
        }
        if (s.has(TamaPet.F_DANCING)) {
            dance(m, s, t);
        }
        if (s.has(TamaPet.F_SCARED)) {
            scared(m, s, t);
        }
        if (s.has(TamaPet.F_BEGGING)) {
            beg(m, s, t);
        }
        if ((s.has(TamaPet.F_CHASING) || s.has(TamaPet.F_AGGRESSIVE)) && !sleeping) {
            crouch(m, s, t);
        }
        if (s.action != null && s.actionT >= 0) {
            action(m, s, s.action, s.actionT, t);
        }
        if (sp == PetSpecies.SCULK_WISP) {
            // always hovering
            root.y += -1.5F + Mth.sin(t * 0.1F) * 0.8F + (sleeping ? 2.5F : 0);
        }
    }

    // ------------------------------------------------------------------ look

    static void look(PetModel m, PetRenderState s, boolean sleeping) {
        if (sleeping) {
            return;
        }
        float yaw = s.yRot * Mth.DEG_TO_RAD;
        float pitch = s.xRot * Mth.DEG_TO_RAD;
        if (bodyLooks(m.species)) {
            rot(m.body, pitch * 0.25F, yaw * 0.45F, 0);
            if (m.species == PetSpecies.MIMIC) {
                rot(m.head, -Math.max(0, -pitch) * 0.5F, 0, 0);   // looking up opens the lid a bit
            }
        } else {
            rot(m.head, pitch, yaw * 0.85F, 0);
        }
    }

    // ------------------------------------------------------------------ idle

    static void idle(PetModel m, PetRenderState s, float t, boolean sleeping) {
        float breathe = Mth.sin(t * (sleeping ? 0.06F : 0.09F));
        if (m.body != null) {
            m.body.y += breathe * (sleeping ? 0.35F : 0.18F);
        }
        float happy = s.tame ? Mth.clamp((s.mood - 40) / 50F, 0, 1) : 0.4F;
        // tail sway: happier pets wag more
        float wag = Mth.sin(t * (0.08F + happy * 0.12F)) * (0.12F + happy * 0.2F);
        rot(m.tail, 0, wag, 0);
        rot(m.tail2, 0, wag * 1.2F, 0);
        rot(m.tail3, 0, wag * 1.3F, 0);
        // ears and frills twitch now and then
        float tw = twitch(t, 0.045F, 1.3F);
        rot(m.earL, 0, 0, tw * 0.35F);
        rot(m.earR, 0, 0, -twitch(t, 0.045F, 2.9F) * 0.35F);
        // wings breathe and sometimes flutter
        float flutter = twitch(t, 0.03F, 0.7F) * Mth.sin(t * 2.2F) * 0.5F;
        rot(m.wingL, 0, 0, breathe * 0.04F + flutter);
        rot(m.wingR, 0, 0, -(breathe * 0.04F + flutter));
        // little extras
        rot(m.scarfTail, Mth.sin(t * 0.07F) * 0.06F, 0, Mth.sin(t * 0.05F) * 0.05F);
        rot(m.antennaL, Mth.sin(t * 0.08F) * 0.08F, 0, Mth.sin(t * 0.11F) * 0.08F);
        rot(m.antennaR, Mth.sin(t * 0.08F + 1.5F) * 0.08F, 0, -Mth.sin(t * 0.11F + 0.7F) * 0.08F);
        rot(m.sproutL, 0, 0, Mth.sin(t * 0.07F) * 0.1F);
        rot(m.sproutR, 0, 0, -Mth.sin(t * 0.07F + 0.5F) * 0.1F);
        rot(m.hatTip, 0, 0, Mth.sin(t * 0.06F) * 0.08F);
        rot(m.crest, Mth.sin(t * 0.06F) * 0.05F, 0, 0);
        // the toad's throat pulses
        if (m.species == PetSpecies.HEX_TOAD && m.head != null) {
            float throat = Math.max(0, Mth.sin(t * 0.18F)) * 0.04F;
            m.head.yScale = 1 + throat;
        }
        // the mimic's lid breathes
        if (m.species == PetSpecies.MIMIC && !sleeping) {
            rot(m.head, -Math.max(0, breathe) * 0.06F, 0, 0);
        }
    }

    // ------------------------------------------------------------------ gaits

    static void gait(PetModel m, PetRenderState s, float pos, float spd, float t) {
        Gait gait = m.species.gait();
        if (gait == Gait.SWIM && s.swimming) {
            float w = t * 0.35F;
            rot(m.body, 0, Mth.sin(w) * 0.08F, 0);
            rot(m.tail, 0, Mth.sin(w - 0.8F) * 0.35F, 0);
            rot(m.tail2, 0, Mth.sin(w - 1.6F) * 0.45F, 0);
            rot(m.tail3, 0.0F, Mth.sin(w - 2.4F) * 0.5F, 0);
            for (ModelPart leg : new ModelPart[]{m.legFL, m.legFR, m.legBL, m.legBR}) {
                if (leg != null) {
                    leg.xRot += 1.1F + Mth.sin(w * 1.5F) * 0.2F;
                }
            }
            rot(m.earL, 0, 0, Mth.sin(w) * 0.25F);
            rot(m.earR, 0, 0, -Mth.sin(w) * 0.25F);
            return;
        }
        switch (gait) {
            case WALK, SWIM -> {
                float c = Mth.cos(pos * 0.6662F) * 1.2F * spd;
                rot(m.legFR, c, 0, 0);
                rot(m.legBL, c, 0, 0);
                rot(m.legFL, -c, 0, 0);
                rot(m.legBR, -c, 0, 0);
                off(m.body, 0, -Math.abs(Mth.sin(pos * 0.6662F)) * 0.7F * spd, 0);
                rot(m.head, Mth.sin(pos * 1.3324F) * 0.06F * spd, 0, 0);
                rot(m.tail, -0.15F * spd, Mth.sin(pos * 0.6662F) * 0.35F * spd, 0);
                rot(m.wingL, 0, 0, -0.25F * spd);
                rot(m.wingR, 0, 0, 0.25F * spd);
                if (m.species == PetSpecies.MIMIC) {
                    rot(m.head, -Math.abs(Mth.sin(pos * 0.6662F)) * 0.18F * spd, 0, 0);   // clack-clack
                    rot(m.body, 0, 0, Mth.sin(pos * 0.6662F) * 0.06F * spd);
                }
            }
            case WADDLE -> {
                float ph = pos * 0.6662F * 1.3F;
                rot(m.body, 0, 0, Mth.sin(ph) * 0.16F * spd);
                rot(m.legL, Mth.cos(ph) * 0.7F * spd, 0, 0);
                rot(m.legR, -Mth.cos(ph) * 0.7F * spd, 0, 0);
                off(m.legL, 0, -Math.max(0, Mth.sin(ph)) * 0.8F * spd, 0);
                off(m.legR, 0, -Math.max(0, -Mth.sin(ph)) * 0.8F * spd, 0);
                rot(m.armL, 0, 0, -(0.25F + Math.abs(Mth.sin(ph)) * 0.35F) * spd);
                rot(m.armR, 0, 0, (0.25F + Math.abs(Mth.sin(ph)) * 0.35F) * spd);
                rot(m.head, 0, 0, -Mth.sin(ph) * 0.08F * spd);
            }
            case HOP -> {
                float h = Math.abs(Mth.sin(pos * 0.45F)) * spd;
                m.rootPart().y -= h * 3.2F;
                rot(m.legBL, h * 0.9F, 0, 0);
                rot(m.legBR, h * 0.9F, 0, 0);
                rot(m.legFL, -h * 0.6F, 0, 0);
                rot(m.legFR, -h * 0.6F, 0, 0);
                rot(m.body, -h * 0.18F, 0, 0);
                rot(m.hat, -h * 0.25F, 0, 0);
            }
            case FLOAT -> {
                rot(m.body, spd * 0.3F, 0, 0);
                rot(m.tail, spd * 0.4F + Mth.sin(t * 0.13F) * 0.15F, 0, 0);
                rot(m.tail2, spd * 0.3F + Mth.sin(t * 0.13F - 0.8F) * 0.2F, 0, 0);
                rot(m.tail3, spd * 0.2F + Mth.sin(t * 0.13F - 1.6F) * 0.25F, 0, 0);
                rot(m.armL, 0, 0, -0.15F - Mth.sin(t * 0.1F) * 0.15F - spd * 0.3F);
                rot(m.armR, 0, 0, 0.15F + Mth.sin(t * 0.1F) * 0.15F + spd * 0.3F);
            }
        }
    }

    // ------------------------------------------------------------------ poses

    static void sitPose(PetModel m, PetRenderState s) {
        switch (m.species) {
            case FROST_PENGUIN, PEBBLE_GOLEM -> {
                off(m.body, 0, 1.4F, 0);
                setX(m.legL, -1.35F);
                setX(m.legR, -1.35F);
                off(m.legL, 0, 0.4F, 0);
                off(m.legR, 0, 0.4F, 0);
            }
            case HEX_TOAD -> off(m.body, 0, 0.6F, 0);
            case SCULK_WISP -> m.rootPart().y += 1.8F;
            case MIMIC -> {
                off(m.body, 0, 2.5F, 0);
                for (ModelPart leg : new ModelPart[]{m.legFL, m.legFR, m.legBL, m.legBR}) {
                    off(leg, 0, -0.5F, 0);
                }
            }
            default -> {
                if (!quadruped(m)) {
                    return;
                }
                rot(m.body, -0.42F, 0, 0);
                off(m.body, 0, 2.0F, 0);
                rot(m.head, 0.42F, 0, 0);
                rot(m.legFL, -0.12F, 0, 0);
                rot(m.legFR, -0.12F, 0, 0);
                for (ModelPart leg : new ModelPart[]{m.legBL, m.legBR}) {
                    leg.xRot = -1.45F;
                    leg.y += 2.6F;
                    leg.z -= 1.0F;
                }
                rot(m.tail, -0.5F, 0, 0);
                rot(m.wingL, 0, 0, -0.35F);
                rot(m.wingR, 0, 0, 0.35F);
            }
        }
    }

    static void sleepPose(PetModel m, PetRenderState s, float t) {
        switch (m.species) {
            case FROST_PENGUIN, PEBBLE_GOLEM -> {
                off(m.body, 0, 1.6F, 0);
                rot(m.body, 0.12F, 0, 0.08F);
                rot(m.head, 0.35F, 0, 0.15F);
                setX(m.legL, -1.4F);
                setX(m.legR, -1.4F);
                off(m.legL, 0, 0.4F, 0);
                off(m.legR, 0, 0.4F, 0);
                rot(m.armL, 0, 0, 0.15F);
                rot(m.armR, 0, 0, -0.15F);
            }
            case HEX_TOAD -> {
                off(m.body, 0, 0.9F, 0);
                rot(m.head, 0.12F, 0, 0);
            }
            case SCULK_WISP -> {
                rot(m.body, 0.18F, 0, 0.1F);
                rot(m.antennaL, 0.5F, 0, 0.2F);
                rot(m.antennaR, 0.5F, 0, -0.2F);
                rot(m.armL, 0, 0, 0.25F);
                rot(m.armR, 0, 0, -0.25F);
            }
            case MIMIC -> {
                off(m.body, 0, 2.5F, 0);
                for (ModelPart leg : new ModelPart[]{m.legFL, m.legFR, m.legBL, m.legBR}) {
                    off(leg, 0, -0.5F, 0);
                }
                rot(m.head, 0.21F, 0, 0);     // lid shut
            }
            default -> {
                if (!quadruped(m)) {
                    return;
                }
                off(m.body, 0, 3.4F, 0);
                rot(m.body, 0.04F, 0, 0);
                m.legFL.xRot = -1.5F;
                m.legFR.xRot = -1.5F;
                m.legBL.xRot = 1.5F;
                m.legBR.xRot = 1.5F;
                for (ModelPart leg : new ModelPart[]{m.legFL, m.legFR, m.legBL, m.legBR}) {
                    leg.y += 2.9F;
                }
                rot(m.head, 0.32F, 0.25F, 0.22F);
                off(m.head, 0, 0.8F, 0);
                rot(m.tail, -0.45F, 0.9F, 0);
                rot(m.tail2, 0, 0.7F, 0);
                rot(m.tail3, 0, 0.5F, 0);
                rot(m.wingL, 0, 0, 0.45F);
                rot(m.wingR, 0, 0, -0.45F);
                rot(m.earL, 0.3F, 0, -0.2F);
                rot(m.earR, 0.3F, 0, 0.2F);
            }
        }
    }

    static void slide(PetModel m, PetRenderState s, float t) {
        // belly slide on snow and ice
        rot(m.body, 1.25F, 0, 0);
        off(m.body, 0, 0.5F, 0);
        rot(m.head, -1.0F, 0, 0);
        setX(m.legL, 1.2F);
        setX(m.legR, 1.2F);
        rot(m.armL, 0, 0, -1.1F);
        rot(m.armR, 0, 0, 1.1F);
    }

    static void dance(PetModel m, PetRenderState s, float t) {
        float b = t * 0.5F;
        rot(m.body, 0, 0, Mth.sin(b) * 0.22F);
        rot(m.head, 0, 0, -Mth.sin(b) * 0.25F);
        m.rootPart().y -= Math.abs(Mth.sin(b)) * 1.6F;
        rot(m.tail, 0, Mth.sin(b * 2) * 0.5F, 0);
        rot(m.armL, 0, 0, -1.2F - Mth.sin(b) * 0.4F);
        rot(m.armR, 0, 0, 1.2F - Mth.sin(b) * 0.4F);
        rot(m.wingL, 0, 0, Mth.sin(b * 2) * 0.35F);
        rot(m.wingR, 0, 0, -Mth.sin(b * 2) * 0.35F);
        rot(m.earL, 0, 0, Mth.sin(b * 2) * 0.3F);
        rot(m.earR, 0, 0, -Mth.sin(b * 2) * 0.3F);
        if (m.species == PetSpecies.MIMIC) {
            rot(m.head, -Math.abs(Mth.sin(b)) * 0.4F, 0, 0);
        }
    }

    static void scared(PetModel m, PetRenderState s, float t) {
        m.rootPart().x += Mth.sin(t * 2.7F) * 0.22F;
        off(m.body, 0, 0.8F, 0);
        rot(m.head, 0.2F, 0, 0);
        rot(m.earL, 0.5F, 0, -0.4F);
        rot(m.earR, 0.5F, 0, 0.4F);
        rot(m.tail, -0.7F, 0, 0);
        rot(m.wingL, 0, 0, -0.5F);
        rot(m.wingR, 0, 0, 0.5F);
        rot(m.armL, 0, 0, 0.2F);
        rot(m.armR, 0, 0, -0.2F);
    }

    static void beg(PetModel m, PetRenderState s, float t) {
        rot(m.head, -0.25F, 0, Mth.sin(t * 0.08F) * 0.28F);
        rot(m.tail, 0, Mth.sin(t * 0.6F) * 0.45F, 0);
        if (quadruped(m) && m.species != PetSpecies.MIMIC && m.species != PetSpecies.HEX_TOAD) {
            rot(m.body, -0.3F, 0, 0);
            rot(m.head, 0.3F, 0, 0);
            m.legFL.xRot = -1.3F + Mth.sin(t * 0.3F) * 0.15F;
            m.legFR.xRot = -1.3F - Mth.sin(t * 0.3F) * 0.15F;
            m.legFL.y -= 1.5F;
            m.legFR.y -= 1.5F;
        }
        rot(m.armL, 0, 0, -0.9F);
        rot(m.armR, 0, 0, 0.9F);
    }

    static void crouch(PetModel m, PetRenderState s, float t) {
        if (quadruped(m) && m.species != PetSpecies.MIMIC) {
            off(m.body, 0, 0.9F, 0);
            rot(m.body, 0.08F, 0, 0);
            rot(m.head, 0.1F, 0, 0);
            rot(m.earL, 0.4F, 0, 0);
            rot(m.earR, 0.4F, 0, 0);
            rot(m.tail, 0.2F, Mth.sin(t * 0.9F) * 0.25F, 0);
        }
        if (m.species == PetSpecies.MIMIC && s.has(TamaPet.F_AGGRESSIVE)) {
            rot(m.head, -Math.abs(Mth.sin(t * 0.35F)) * 0.45F, 0, 0);   // menacing chomps
        }
    }

    // ------------------------------------------------------------------ one-shot actions

    static void action(PetModel m, PetRenderState s, PetAction a, float t, float time) {
        float e = env(t);
        ModelPart root = m.rootPart();
        PetSpecies sp = m.species;
        switch (a) {
            case PETTED, GROOMED -> {
                rot(m.head, -0.35F * e, 0, Mth.sin(t * PI * 3) * 0.3F * e);
                rot(m.body, 0, 0, Mth.sin(t * PI * 6) * 0.07F * e);
                rot(m.tail, 0.2F * e, Mth.sin(t * PI * 10) * 0.6F * e, 0);
                rot(m.earL, -0.3F * e, 0, 0.25F * e);
                rot(m.earR, -0.3F * e, 0, -0.25F * e);
                rot(m.wingL, 0, 0, Mth.sin(t * PI * 8) * 0.3F * e);
                rot(m.wingR, 0, 0, -Mth.sin(t * PI * 8) * 0.3F * e);
                rot(m.armL, 0, 0, -0.8F * e);
                rot(m.armR, 0, 0, 0.8F * e);
                root.y -= hop(t, 0.72F, 1.0F) * 2.2F;
                if (sp == PetSpecies.MIMIC) {
                    rot(m.head, -0.3F * e, 0, 0);
                    off(m.tongue, 0, 0, -2.5F * e);
                    rot(m.tongue, 0.3F * e, 0, 0);
                }
                if (sp == PetSpecies.HEX_TOAD && m.head != null) {
                    m.head.yScale *= 1 + 0.12F * e;
                }
            }
            case EAT -> {
                float nod = 0.55F + 0.25F * Mth.sin(t * PI * 6);
                if (bodyLooks(sp)) {
                    rot(m.body, 0.25F * e * nod, 0, 0);
                } else {
                    rot(m.head, nod * e, 0, 0);
                }
                rot(m.jaw, Math.max(0, Mth.sin(t * PI * 12)) * 0.45F * e, 0, 0);
                if (sp == PetSpecies.MIMIC) {
                    rot(m.head, -Math.max(0, Mth.sin(t * PI * 8)) * 0.6F * e, 0, 0);
                }
                if (sp == PetSpecies.HEX_TOAD && m.tongue != null && t > 0.2F && t < 0.45F) {
                    m.tongue.visible = true;
                    m.tongue.zScale = 0.3F + env(ramp(t, 0.2F, 0.45F)) * 0.8F;
                    m.tongue.xRot += 0.6F;
                }
                rot(m.tail, 0, Mth.sin(t * PI * 8) * 0.3F * e, 0);
            }
            case ATTACK -> {
                float wind = t < 0.4F ? ramp(t, 0, 0.4F) : 1 - ramp(t, 0.4F, 0.55F);
                float strike = hop(t, 0.4F, 0.8F);
                off(m.body, 0, 0, 1.2F * wind - 2.2F * strike);
                rot(m.head, -0.3F * wind + 0.35F * strike, 0, 0);
                rot(m.jaw, 0.7F * strike, 0, 0);
                rot(m.earL, 0.4F * e, 0, 0);
                rot(m.earR, 0.4F * e, 0, 0);
                if (sp == PetSpecies.MIMIC) {
                    rot(m.head, -1.0F * wind + 0.9F * strike, 0, 0);
                }
                if (sp == PetSpecies.FROST_PENGUIN) {
                    rot(m.armR, -2.6F * wind + 2.0F * strike, 0, 0.3F * e);
                }
                if (sp == PetSpecies.PEBBLE_GOLEM) {
                    rot(m.armL, -2.4F * wind + 2.4F * strike, 0, 0);
                    rot(m.armR, -2.4F * wind + 2.4F * strike, 0, 0);
                    root.y -= hop(t, 0.1F, 0.5F) * 3.0F;
                }
                if (sp == PetSpecies.HEX_TOAD && m.tongue != null) {
                    m.tongue.visible = t > 0.35F && t < 0.85F;
                    m.tongue.zScale = 0.2F + hop(t, 0.35F, 0.85F) * 2.6F;
                }
            }
            case BREATH -> {
                rot(m.head, -0.18F * e, 0, 0);
                rot(m.jaw, 0.65F * e, 0, 0);
                off(m.body, 0, 0, 0.8F * e);
                rot(m.wingL, 0, 0, -0.5F * e);
                rot(m.wingR, 0, 0, 0.5F * e);
                rot(m.antennaL, -0.4F * e, 0, 0.3F * e);
                rot(m.antennaR, -0.4F * e, 0, -0.3F * e);
                if (sp == PetSpecies.SCULK_WISP) {
                    rot(m.body, -0.2F * e, 0, 0);
                    rot(m.armL, 0, 0, -1.0F * e);
                    rot(m.armR, 0, 0, 1.0F * e);
                }
            }
            case TALENT -> talent(m, s, t, e, time);
            case FEED_OWNER -> {
                if (quadruped(m) && sp != PetSpecies.MIMIC) {
                    rot(m.body, -0.6F * e, 0, 0);
                    rot(m.head, 0.3F * e, 0, 0);
                    m.legFL.xRot -= 1.1F * e;
                    m.legFR.xRot -= 1.1F * e;
                    m.legFL.y -= 2F * e;
                    m.legFR.y -= 2F * e;
                } else {
                    rot(m.armL, -1.5F * e, 0, -0.3F * e);
                    rot(m.armR, -1.5F * e, 0, 0.3F * e);
                    rot(m.head, -0.4F * e, 0, 0);
                }
                if (sp == PetSpecies.MIMIC) {
                    rot(m.head, -0.9F * e, 0, 0);
                }
                rot(m.tail, 0, Mth.sin(t * PI * 8) * 0.4F * e, 0);
            }
            case CELEBRATE, TAMED -> {
                float jumps = a == PetAction.TAMED ? 2 : 1;
                float jt = (t * jumps) % 1F;
                root.y -= hop(jt, 0.1F, 0.9F) * 5.5F;
                rot(m.body, 0, hop(jt, 0.1F, 0.9F) > 0 ? ramp(jt, 0.1F, 0.9F) * Mth.TWO_PI : 0, 0);
                rot(m.wingL, 0, 0, Mth.sin(t * PI * 12) * 0.6F * e);
                rot(m.wingR, 0, 0, -Mth.sin(t * PI * 12) * 0.6F * e);
                rot(m.armL, 0, 0, -1.6F * e);
                rot(m.armR, 0, 0, 1.6F * e);
                rot(m.tail, 0.3F * e, Mth.sin(t * PI * 10) * 0.5F * e, 0);
                rot(m.head, -0.3F * e, 0, 0);
                if (sp == PetSpecies.MIMIC) {
                    rot(m.head, -0.8F * e, 0, 0);
                }
            }
            case SNIFF -> {
                float twitchy = Mth.sin(t * PI * 22) * 0.05F * e;
                if (bodyLooks(sp)) {
                    rot(m.body, 0.3F * e + twitchy, Mth.sin(t * PI * 3) * 0.3F * e, 0);
                } else {
                    rot(m.head, 0.55F * e + twitchy, Mth.sin(t * PI * 3) * 0.35F * e, 0);
                }
                rot(m.earL, -0.25F * e, 0, 0);
                rot(m.earR, -0.25F * e, 0, 0);
                rot(m.tail, 0.25F * e, 0, 0);
            }
            case POUNCE -> {
                float crouch = 1 - ramp(t, 0.35F, 0.45F);
                float leap = hop(t, 0.4F, 0.95F);
                off(m.body, 0, 1.6F * crouch * ramp(t, 0, 0.2F), 0);
                rot(m.body, 0, 0, Mth.sin(t * PI * 10) * 0.08F * crouch);     // butt wiggle
                rot(m.body, -0.35F * leap, 0, 0);
                root.y -= leap * 4.0F;
                rot(m.legFL, -1.0F * leap, 0, 0);
                rot(m.legFR, -1.0F * leap, 0, 0);
                rot(m.legBL, 0.8F * leap, 0, 0);
                rot(m.legBR, 0.8F * leap, 0, 0);
                rot(m.armL, 0, 0, -1.3F * leap);
                rot(m.armR, 0, 0, 1.3F * leap);
                rot(m.tail, 0.5F * leap, 0, 0);
            }
            case SHAKE -> {
                float sh = Mth.sin(t * PI * 16) * e;
                rot(m.body, 0, 0, sh * 0.42F);
                rot(m.head, 0, 0, Mth.sin(t * PI * 16 + 0.6F) * 0.35F * e);
                rot(m.earL, 0, 0, sh * 0.5F);
                rot(m.earR, 0, 0, sh * 0.5F);
                rot(m.tail, 0, sh * 0.6F, 0);
                rot(m.wingL, 0, 0, sh * 0.4F);
                rot(m.wingR, 0, 0, sh * 0.4F);
                rot(m.armL, 0, 0, -0.6F * e);
                rot(m.armR, 0, 0, 0.6F * e);
            }
            case SCRATCH -> {
                if (quadruped(m) && sp != PetSpecies.MIMIC && sp != PetSpecies.HEX_TOAD) {
                    rot(m.body, -0.75F * e, 0, 0);
                    rot(m.head, 0.45F * e, 0, 0);
                    m.legFL.xRot += (-1.7F + Mth.sin(t * PI * 16) * 0.45F) * e;
                    m.legFR.xRot += (-1.7F - Mth.sin(t * PI * 16) * 0.45F) * e;
                    m.legFL.y -= 2.4F * e;
                    m.legFR.y -= 2.4F * e;
                } else {
                    rot(m.armL, (-1.6F + Mth.sin(t * PI * 16) * 0.5F) * e, 0, 0);
                    rot(m.armR, (-1.6F - Mth.sin(t * PI * 16) * 0.5F) * e, 0, 0);
                    rot(m.body, 0, 0, Mth.sin(t * PI * 8) * 0.1F * e);
                }
                rot(m.tail, 0, Mth.sin(t * PI * 6) * 0.3F * e, 0);
            }
            case YAWN -> {
                rot(m.head, -0.45F * e, 0, 0);
                rot(m.jaw, 0.7F * e, 0, 0);
                rot(m.legFL, -0.4F * e, 0, 0);
                rot(m.legFR, -0.4F * e, 0, 0);
                rot(m.armL, 0, 0, -1.0F * e);
                rot(m.armR, 0, 0, 1.0F * e);
                rot(m.wingL, 0, 0, 0.5F * e);
                rot(m.wingR, 0, 0, -0.5F * e);
                if (sp == PetSpecies.MIMIC) {
                    rot(m.head, -0.7F * e, 0, 0);
                }
            }
            case BOUNCE -> {
                float squash = Mth.sin(t * PI);
                if (m.body != null) {
                    m.body.yScale *= 1 - 0.18F * squash;
                    m.body.xScale *= 1 + 0.1F * squash;
                    m.body.zScale *= 1 + 0.1F * squash;
                }
                rot(m.armL, 0, 0, -1.4F * squash);
                rot(m.armR, 0, 0, 1.4F * squash);
                rot(m.wingL, 0, 0, -0.6F * squash);
                rot(m.wingR, 0, 0, 0.6F * squash);
            }
            case COUGH -> {
                float jolt = hop(t, 0.3F, 0.55F);
                rot(m.head, -1.0F * jolt, 0, 0);
                off(m.body, 0, 0, 0.8F * jolt);
                rot(m.jaw, 0.5F * jolt, 0, 0);
            }
            case LOOK_UP -> {
                if (bodyLooks(sp)) {
                    rot(m.body, -0.35F * e, 0, 0);
                } else {
                    rot(m.head, -0.75F * e, 0, 0);
                }
                rot(m.earL, -0.4F * e, 0, 0);
                rot(m.earR, -0.4F * e, 0, 0);
                root.y -= hop(t, 0.5F, 0.8F) * 1.5F;
            }
            case PLAY -> {
                float bow = env(ramp(t, 0, 0.6F));
                if (quadruped(m) && sp != PetSpecies.MIMIC) {
                    rot(m.body, 0.35F * bow, 0, 0);
                    rot(m.head, -0.35F * bow, 0, 0);
                    m.legFL.xRot -= 0.9F * bow;
                    m.legFR.xRot -= 0.9F * bow;
                }
                rot(m.tail, 0.5F * e, Mth.sin(t * PI * 10) * 0.6F * e, 0);
                rot(m.armL, 0, 0, -1.2F * e);
                rot(m.armR, 0, 0, 1.2F * e);
                root.y -= hop(t, 0.65F, 1.0F) * 3F;
                if (sp == PetSpecies.MIMIC) {
                    rot(m.head, -Math.abs(Mth.sin(t * PI * 4)) * 0.6F, 0, 0);
                }
            }
        }
    }

    static void talent(PetModel m, PetRenderState s, float t, float e, float time) {
        ModelPart root = m.rootPart();
        switch (m.species) {
            case DESERT_DRAGON, EMBER_PUP -> {
                rot(m.head, -0.6F * e, 0, 0);
                rot(m.jaw, 0.6F * e, 0, 0);
                rot(m.wingL, 0, 0, Mth.sin(t * PI * 10) * 0.5F * e);
                rot(m.wingR, 0, 0, -Mth.sin(t * PI * 10) * 0.5F * e);
                rot(m.tail, 0.4F * e, 0, 0);
            }
            case JUNGLE_DRAGON -> {
                root.y -= hop(t, 0.2F, 0.7F) * 3F;
                rot(m.wingL, 0, 0, Mth.sin(t * PI * 12) * 0.6F * e);
                rot(m.wingR, 0, 0, -Mth.sin(t * PI * 12) * 0.6F * e);
                rot(m.head, -0.4F * e, 0, 0);
                rot(m.crest, -0.4F * e, 0, 0);
            }
            case TIDE_DRAGON -> {
                rot(m.body, 0, ramp(t, 0.1F, 0.9F) * Mth.TWO_PI, 0);
                root.y -= hop(t, 0.1F, 0.9F) * 2.5F;
                rot(m.earL, 0, 0, 0.5F * e);
                rot(m.earR, 0, 0, -0.5F * e);
            }
            case FROST_PENGUIN -> {
                rot(m.armL, 0, 0, -1.3F * e - Mth.sin(t * PI * 10) * 0.4F * e);
                rot(m.armR, 0, 0, 1.3F * e + Mth.sin(t * PI * 10) * 0.4F * e);
                rot(m.head, -0.35F * e, 0, 0);
                root.y -= hop(t, 0.3F, 0.7F) * 2F;
            }
            case SCULK_WISP -> {
                rot(m.antennaL, -0.6F * e, 0, 0.5F * e);
                rot(m.antennaR, -0.6F * e, 0, -0.5F * e);
                rot(m.armL, 0, 0, -1.3F * e);
                rot(m.armR, 0, 0, 1.3F * e);
                root.y -= 2.5F * e;
                if (m.body != null) {
                    float pulse = 1 + 0.08F * Mth.sin(t * PI * 6) * e;
                    m.body.xScale *= pulse;
                    m.body.yScale *= pulse;
                    m.body.zScale *= pulse;
                }
            }
            case VOID_KITTEN -> {
                if (m.body != null) {
                    float pop = 1 - 0.35F * hop(t, 0.2F, 0.6F);
                    m.body.xScale *= pop;
                    m.body.yScale *= pop;
                    m.body.zScale *= pop;
                }
                rot(m.tail, 0.6F * e, Mth.sin(t * PI * 6) * 0.5F * e, 0);
            }
            case PEBBLE_GOLEM -> {
                rot(m.body, 0.3F * e + Mth.sin(t * PI * 18) * 0.04F * e, 0, 0);
                rot(m.sproutL, 0, 0, 0.6F * e);
                rot(m.sproutR, 0, 0, -0.6F * e);
            }
            case HEX_TOAD -> {
                if (m.body != null) {
                    float puff = 1 + 0.18F * hop(t, 0.1F, 0.6F);
                    m.body.xScale *= puff;
                    m.body.zScale *= puff;
                }
                root.y -= hop(t, 0.6F, 0.95F) * 3F;
                rot(m.hat, -0.3F * e, 0, 0.2F * e);
            }
            case MIMIC -> {
                rot(m.head, -1.1F * e, 0, 0);
                rot(m.body, 0, 0, Mth.sin(t * PI * 8) * 0.1F * e);
            }
        }
    }
}
