package net.kasax.tamagotchi.pet;

import net.minecraft.util.Mth;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/** The Tamagotchi part: four needs (0..100) that drain over time, a mood made from them, and bond. */
public final class PetNeeds {
    public enum Need { HUNGER, FUN, ENERGY, HYGIENE }

    public enum Mood {
        MISERABLE, SAD, OKAY, HAPPY, ECSTATIC;

        public static Mood of(float value) {
            if (value >= 85) return ECSTATIC;
            if (value >= 60) return HAPPY;
            if (value >= 35) return OKAY;
            if (value >= 15) return SAD;
            return MISERABLE;
        }

        public boolean atLeast(Mood other) {
            return ordinal() >= other.ordinal();
        }
    }

    /** Per-second drain. Full to empty: hunger 75 min, fun 50 min, energy 60 min, hygiene 90 min. */
    private static final float HUNGER_DRAIN = 100F / 4500F;
    private static final float FUN_DRAIN = 100F / 3000F;
    private static final float ENERGY_DRAIN = 100F / 3600F;
    private static final float HYGIENE_DRAIN = 100F / 5400F;

    public float hunger = 80;
    public float fun = 80;
    public float energy = 90;
    public float hygiene = 90;
    public float bond = 0;

    public void tickSecond(boolean sleeping, boolean sitting) {
        this.hunger -= HUNGER_DRAIN * (sleeping ? 0.5F : 1F);
        this.fun -= FUN_DRAIN * (sleeping ? 0.2F : 1F);
        this.hygiene -= HYGIENE_DRAIN;
        if (sleeping) {
            this.energy += 100F / 240F;      // a nap of four minutes fills it up
        } else if (sitting) {
            this.energy += 0.05F;
        } else {
            this.energy -= ENERGY_DRAIN;
        }
        clamp();
    }

    public void add(Need need, float amount) {
        switch (need) {
            case HUNGER -> this.hunger += amount;
            case FUN -> this.fun += amount;
            case ENERGY -> this.energy += amount;
            case HYGIENE -> this.hygiene += amount;
        }
        clamp();
    }

    public float get(Need need) {
        return switch (need) {
            case HUNGER -> this.hunger;
            case FUN -> this.fun;
            case ENERGY -> this.energy;
            case HYGIENE -> this.hygiene;
        };
    }

    public void addBond(float amount) {
        this.bond = Mth.clamp(this.bond + amount, 0, 100);
    }

    public float moodValue() {
        return moodValue(this.hunger, this.fun, this.energy, this.hygiene);
    }

    public static float moodValue(float hunger, float fun, float energy, float hygiene) {
        return 0.3F * hunger + 0.3F * fun + 0.2F * energy + 0.2F * hygiene;
    }

    public Mood mood() {
        return Mood.of(moodValue());
    }

    /** The need that is lowest right now (for emotes and pager beeps). */
    public Need lowest() {
        Need low = Need.HUNGER;
        for (Need n : Need.values()) {
            if (get(n) < get(low)) {
                low = n;
            }
        }
        return low;
    }

    private void clamp() {
        this.hunger = Mth.clamp(this.hunger, 0, 100);
        this.fun = Mth.clamp(this.fun, 0, 100);
        this.energy = Mth.clamp(this.energy, 0, 100);
        this.hygiene = Mth.clamp(this.hygiene, 0, 100);
    }

    /** Packs the four needs into one int for the synced entity data. */
    public int pack() {
        return (Math.round(this.hunger) & 0xFF) | (Math.round(this.fun) & 0xFF) << 8
                | (Math.round(this.energy) & 0xFF) << 16 | (Math.round(this.hygiene) & 0xFF) << 24;
    }

    public static int unpack(int packed, Need need) {
        return (packed >>> (need.ordinal() * 8)) & 0xFF;
    }

    public void save(ValueOutput out) {
        out.putFloat("Hunger", this.hunger);
        out.putFloat("Fun", this.fun);
        out.putFloat("Energy", this.energy);
        out.putFloat("Hygiene", this.hygiene);
        out.putFloat("Bond", this.bond);
    }

    public void load(ValueInput in) {
        this.hunger = in.getFloatOr("Hunger", 80);
        this.fun = in.getFloatOr("Fun", 80);
        this.energy = in.getFloatOr("Energy", 90);
        this.hygiene = in.getFloatOr("Hygiene", 90);
        this.bond = in.getFloatOr("Bond", 0);
    }
}
