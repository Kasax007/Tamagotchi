package net.kasax.tamagotchi.registry;

import java.util.HashMap;
import java.util.Map;
import net.kasax.tamagotchi.Tamagotchi;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.sounds.SoundEvent;

/** Every sound event of the mod; the files and pitch tweaks live in assets/tamagotchi/sounds.json. */
public final class ModSounds {
    private static final Map<String, SoundEvent> BY_NAME = new HashMap<>();

    public static final SoundEvent PET_PETTING = reg("pet.petting");
    public static final SoundEvent PET_EAT = reg("pet.eat");
    public static final SoundEvent PET_YAWN = reg("pet.yawn");
    public static final SoundEvent PET_SNORE = reg("pet.snore");
    public static final SoundEvent PET_SPLASH = reg("pet.splash");
    public static final SoundEvent PET_SHAKE = reg("pet.shake");
    public static final SoundEvent PET_TAME = reg("pet.tame");
    public static final SoundEvent PET_FAINT = reg("pet.faint");
    public static final SoundEvent PET_WAKE = reg("pet.wake");
    public static final SoundEvent PET_CELEBRATE = reg("pet.celebrate");
    public static final SoundEvent PET_SCARED = reg("pet.scared");
    public static final SoundEvent PET_FEED_OWNER = reg("pet.feed_owner");
    public static final SoundEvent PAGER_BEEP = reg("pager.beep");
    public static final SoundEvent PAGER_OPEN = reg("pager.open");
    public static final SoundEvent TOY_SQUEAK = reg("toy.squeak");
    public static final SoundEvent TOY_LASER = reg("toy.laser");
    public static final SoundEvent TOY_FEATHER = reg("toy.feather");
    public static final SoundEvent BLOCK_BOUNCE = reg("block.bounce");
    public static final SoundEvent BLOCK_WHEEL = reg("block.wheel");
    public static final SoundEvent BLOCK_BOWL_FILL = reg("block.bowl_fill");
    public static final SoundEvent ITEM_BRUSH = reg("item.brush");
    public static final SoundEvent BACKPACK_EQUIP = reg("backpack.equip");
    public static final SoundEvent BACKPACK_SPILL = reg("backpack.spill");
    public static final SoundEvent TALENT_ROAST = reg("talent.roast");
    public static final SoundEvent TALENT_GROW = reg("talent.grow");
    public static final SoundEvent TALENT_BLESSING = reg("talent.blessing");
    public static final SoundEvent TALENT_FREEZE = reg("talent.freeze");
    public static final SoundEvent TALENT_WARM = reg("talent.warm");
    public static final SoundEvent TALENT_PING = reg("talent.ping");
    public static final SoundEvent TALENT_MAGNET = reg("talent.magnet");
    public static final SoundEvent TALENT_SNIFF = reg("talent.sniff");
    public static final SoundEvent TALENT_BREW = reg("talent.brew");
    public static final SoundEvent TALENT_TREASURE = reg("talent.treasure");

    static {
        for (PetSpecies s : PetSpecies.values()) {
            for (String kind : new String[]{"ambient", "happy", "hurt", "death", "attack"}) {
                reg(s.id() + "." + kind);
            }
        }
    }

    private ModSounds() {
    }

    private static SoundEvent reg(String name) {
        Identifier id = Tamagotchi.id(name);
        SoundEvent ev = SoundEvent.createVariableRangeEvent(id);
        BY_NAME.put(name, ev);
        return ev;
    }

    public static SoundEvent species(PetSpecies s, String kind) {
        return BY_NAME.get(s.id() + "." + kind);
    }

    public static void initialize() {
        for (Map.Entry<String, SoundEvent> e : BY_NAME.entrySet()) {
            Registry.register(BuiltInRegistries.SOUND_EVENT, Tamagotchi.id(e.getKey()), e.getValue());
        }
    }
}
