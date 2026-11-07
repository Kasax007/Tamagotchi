package net.kasax.tamacraft.registry;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import net.kasax.tamacraft.Tamacraft;
import net.kasax.tamacraft.item.FeatherWandItem;
import net.kasax.tamacraft.item.LaserPointerItem;
import net.kasax.tamacraft.item.PetFoodItem;
import net.kasax.tamacraft.item.SqueakyBallItem;
import net.kasax.tamacraft.item.TamaEggItem;
import net.kasax.tamacraft.item.TamaPagerItem;
import net.kasax.tamacraft.item.TooltipItem;
import net.kasax.tamacraft.pet.PetSpecies;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.SpawnEggItem;

/** All items. Order of declaration = order in the creative tab. */
public final class ModItems {
    public static final List<Item> TAB_ORDER = new ArrayList<>();

    public static final Item TAMACRAFT_HEART = reg("tamacraft_heart", TooltipItem::new, new Item.Properties().stacksTo(16).rarity(Rarity.UNCOMMON));
    public static final Item TAMA_PAGER = reg("tama_pager", TamaPagerItem::new, new Item.Properties().stacksTo(1));
    public static final Item TAMACON = reg("tamacon", net.kasax.tamacraft.item.TamaconItem::new, new Item.Properties().stacksTo(1));
    public static final Item PET_BRUSH = reg("pet_brush", TooltipItem::new, new Item.Properties().durability(160));
    public static final Item LASER_POINTER = reg("laser_pointer", LaserPointerItem::new, new Item.Properties().stacksTo(1));
    public static final Item SQUEAKY_BALL = reg("squeaky_ball", SqueakyBallItem::new, new Item.Properties().stacksTo(16));
    public static final Item FEATHER_WAND = reg("feather_wand", FeatherWandItem::new, new Item.Properties().stacksTo(1));
    public static final Item PET_KIBBLE = reg("pet_kibble", PetFoodItem::new, new Item.Properties());
    public static final Item FISH_CRACKERS = reg("fish_crackers", PetFoodItem::new, new Item.Properties());
    public static final Item DRAGON_FRUIT = reg("dragon_fruit", PetFoodItem::new, new Item.Properties());
    public static final Item EMBER_JERKY = reg("ember_jerky", PetFoodItem::new, new Item.Properties().fireResistant());
    public static final Item ROCK_CANDY = reg("rock_candy", PetFoodItem::new, new Item.Properties());
    public static final Item GLOW_GUMMY = reg("glow_gummy", PetFoodItem::new, new Item.Properties());
    public static final Item GOLDEN_BISCUIT = reg("golden_biscuit", PetFoodItem::new, new Item.Properties().rarity(Rarity.UNCOMMON));
    public static final Item TAMA_EGG = regHidden("tama_egg", TamaEggItem::new, new Item.Properties().stacksTo(1).fireResistant().rarity(Rarity.RARE));

    public static final Map<PetSpecies, Item> SPAWN_EGGS = new EnumMap<>(PetSpecies.class);

    private ModItems() {
    }

    static Item reg(String name, Function<Item.Properties, Item> factory, Item.Properties props) {
        Item item = regHidden(name, factory, props);
        TAB_ORDER.add(item);
        return item;
    }

    static Item regHidden(String name, Function<Item.Properties, Item> factory, Item.Properties props) {
        ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, Tamacraft.id(name));
        Item item = factory.apply(props);
        Registry.register(BuiltInRegistries.ITEM, key, item);
        return item;
    }

    public static void initialize() {
        for (PetSpecies s : PetSpecies.values()) {
            SPAWN_EGGS.put(s, regHidden(s.id() + "_spawn_egg", p -> new SpawnEggItem(ModEntities.type(s), 0xFFFFFF, 0xFFFFFF, p), new Item.Properties()));
        }
    }
}
