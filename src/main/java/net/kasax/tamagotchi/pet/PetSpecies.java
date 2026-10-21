package net.kasax.tamagotchi.pet;

import java.util.List;
import java.util.Locale;
import java.util.function.Predicate;
import java.util.function.Supplier;
import net.kasax.tamagotchi.Tamagotchi;
import net.kasax.tamagotchi.registry.ModItems;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.tags.ItemTags;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/**
 * Everything that makes one pet different from another. One {@code EntityType} per species, all
 * backed by the shared {@link TamaPet} class, which looks its species up from its type.
 */
public enum PetSpecies {
    DESERT_DRAGON(new Props("desert_dragon").size(0.7F, 0.85F).gait(Gait.WALK).stats(30, 4, 0.28)
            .attack(AttackStyle.FIRE_BREATH).diet(Diet.MEAT).treat(() -> ModItems.DRAGON_FRUIT).color(0xE6BE80)
            .fireImmune().names("Sandy", "Dune", "Saffron", "Sunny", "Pharaoh", "Nugget", "Biscuit", "Cleo")),
    JUNGLE_DRAGON(new Props("jungle_dragon").size(0.7F, 0.85F).gait(Gait.WALK).stats(30, 4, 0.30)
            .attack(AttackStyle.POISON_BITE).diet(Diet.PLANT).treat(() -> ModItems.DRAGON_FRUIT).color(0x5DAA3C)
            .names("Fern", "Kiwi", "Basil", "Ivy", "Mango", "Clover", "Sprout", "Lime")),
    TIDE_DRAGON(new Props("tide_dragon").size(0.7F, 0.85F).gait(Gait.SWIM).stats(30, 4, 0.28)
            .attack(AttackStyle.BUBBLE).diet(Diet.FISH).treat(() -> ModItems.FISH_CRACKERS).color(0x3AA7B3)
            .waterBreathing().names("Splash", "Coral", "Marina", "Bubbles", "Nami", "Pearl", "Wave", "Finn")),
    FROST_PENGUIN(new Props("frost_penguin").size(0.55F, 0.8F).gait(Gait.WADDLE).stats(24, 3, 0.25)
            .attack(AttackStyle.SNOWBALL).diet(Diet.FISH).treat(() -> ModItems.FISH_CRACKERS).color(0x2F3D5C)
            .names("Pip", "Waddles", "Snowball", "Flurry", "Pingu", "Frosty", "Mochi", "Sleet")),
    EMBER_PUP(new Props("ember_pup").size(0.6F, 0.8F).gait(Gait.WALK).stats(28, 5, 0.32)
            .attack(AttackStyle.BURN_BITE).diet(Diet.MEAT).treat(() -> ModItems.EMBER_JERKY).color(0xFF8A2A)
            .fireImmune().names("Cinder", "Ash", "Scorch", "Magma", "Blaze", "Ember", "Sparky", "Coal")),
    SCULK_WISP(new Props("sculk_wisp").size(0.55F, 0.8F).gait(Gait.FLOAT).stats(22, 4, 0.30)
            .attack(AttackStyle.SONIC).diet(Diet.SWEET).treat(() -> ModItems.GLOW_GUMMY).color(0x2EE6F0)
            .flying().names("Echo", "Murmur", "Hush", "Wisp", "Blip", "Shade", "Ping", "Lumen")),
    VOID_KITTEN(new Props("void_kitten").size(0.5F, 0.65F).gait(Gait.WALK).stats(22, 4, 0.33)
            .attack(AttackStyle.BLINK).diet(Diet.FISH).treat(() -> ModItems.FISH_CRACKERS).color(0xE05BFF)
            .names("Nyx", "Luna", "Starla", "Comet", "Vega", "Nova", "Orbit", "Mimi")),
    PEBBLE_GOLEM(new Props("pebble_golem").size(0.6F, 0.75F).gait(Gait.WADDLE).stats(40, 4, 0.22)
            .attack(AttackStyle.SLAM).diet(Diet.MINERAL).treat(() -> ModItems.ROCK_CANDY).color(0x8E8E92)
            .armor(6).names("Pebble", "Rocky", "Flint", "Gravel", "Cobble", "Boulder", "Mossy", "Pumice")),
    HEX_TOAD(new Props("hex_toad").size(0.6F, 0.55F).gait(Gait.HOP).stats(24, 3, 0.26)
            .attack(AttackStyle.TONGUE).diet(Diet.SWEET).treat(() -> ModItems.GLOW_GUMMY).color(0x6E8F3E)
            .names("Hex", "Bramble", "Toadstool", "Wartson", "Bog", "Pickle", "Murky", "Elixir")),
    MIMIC(new Props("mimic").size(0.7F, 0.75F).gait(Gait.WALK).stats(34, 6, 0.24)
            .attack(AttackStyle.CHOMP).diet(Diet.ANY).treat(() -> ModItems.GOLDEN_BISCUIT).color(0xE8B84A)
            .waterBreathing().belly().names("Chompy", "Munch", "Goldie", "Gulp", "Biscuit", "Lockjaw", "Coffer", "Trinket"));

    public enum Gait { WALK, WADDLE, HOP, FLOAT, SWIM }

    public enum AttackStyle {
        FIRE_BREATH(4.5, true), POISON_BITE(2.0, false), BUBBLE(4.5, true), SNOWBALL(6.0, true), BURN_BITE(2.0, false),
        SONIC(5.0, true), BLINK(2.0, false), SLAM(2.2, false), TONGUE(3.5, true), CHOMP(2.0, false);

        public final double range;
        public final boolean ranged;

        AttackStyle(double range, boolean ranged) {
            this.range = range;
            this.ranged = ranged;
        }
    }

    public enum Diet {
        MEAT(s -> s.is(ItemTags.MEAT)),
        FISH(s -> s.is(ItemTags.FISHES)),
        PLANT(s -> s.is(Items.SWEET_BERRIES) || s.is(Items.APPLE) || s.is(Items.MELON_SLICE) || s.is(Items.CARROT)
                || s.is(Items.BEETROOT) || s.is(Items.GLOW_BERRIES)),
        SWEET(s -> s.is(Items.COOKIE) || s.is(Items.HONEY_BOTTLE) || s.is(Items.SWEET_BERRIES) || s.is(Items.GLOW_BERRIES)
                || s.is(Items.PUMPKIN_PIE)),
        MINERAL(s -> s.is(Items.FLINT) || s.is(Items.AMETHYST_SHARD) || s.is(Items.CLAY_BALL) || s.is(Items.QUARTZ)),
        ANY(s -> s.has(DataComponents.FOOD));

        private final Predicate<ItemStack> test;

        Diet(Predicate<ItemStack> test) {
            this.test = test;
        }

        public boolean accepts(ItemStack stack) {
            return this.test.test(stack);
        }
    }

    private final Props props;

    PetSpecies(Props props) {
        this.props = props;
    }

    public String id() {
        return this.props.id;
    }

    public Identifier key() {
        return Tamagotchi.id(this.props.id);
    }

    public Component displayName() {
        return Component.translatable("entity.tamagotchi." + this.props.id);
    }

    public Component talentName() {
        return Component.translatable("talent.tamagotchi." + this.props.id);
    }

    public Component talentDescription() {
        return Component.translatable("talent.tamagotchi." + this.props.id + ".desc");
    }

    public float width() { return this.props.width; }
    public float height() { return this.props.height; }
    public Gait gait() { return this.props.gait; }
    public double maxHealth() { return this.props.health; }
    public double attackDamage() { return this.props.damage; }
    public double speed() { return this.props.speed; }
    public double armor() { return this.props.armor; }
    public AttackStyle attackStyle() { return this.props.attack; }
    public Diet diet() { return this.props.diet; }
    public Item favoriteTreat() { return this.props.treat.get(); }
    public int color() { return this.props.color; }
    public boolean fireImmune() { return this.props.fireImmune; }
    public boolean waterBreathing() { return this.props.waterBreathing; }
    public boolean flying() { return this.props.flying; }

    /** The dragons: they fly when it is faster or when they feel like it. */
    public boolean winged() { return this == DESERT_DRAGON || this == JUNGLE_DRAGON || this == TIDE_DRAGON; }
    /** The mimic carries 27 slots in its belly even without a backpack. */
    public boolean hasBelly() { return this.props.belly; }
    public List<String> names() { return this.props.names; }

    public static PetSpecies byId(String id) {
        for (PetSpecies s : values()) {
            if (s.id().equals(id)) {
                return s;
            }
        }
        return null;
    }

    public String lowerName() {
        return name().toLowerCase(Locale.ROOT);
    }

    static final class Props {
        final String id;
        float width = 0.6F;
        float height = 0.8F;
        Gait gait = Gait.WALK;
        double health = 24;
        double damage = 4;
        double speed = 0.28;
        double armor = 0;
        AttackStyle attack = AttackStyle.CHOMP;
        Diet diet = Diet.ANY;
        Supplier<Item> treat = () -> Items.COOKIE;
        int color = 0xFFFFFF;
        boolean fireImmune;
        boolean waterBreathing;
        boolean flying;
        boolean belly;
        List<String> names = List.of("Buddy");

        Props(String id) {
            this.id = id;
        }

        Props size(float w, float h) { this.width = w; this.height = h; return this; }
        Props gait(Gait g) { this.gait = g; return this; }
        Props stats(double hp, double dmg, double speed) { this.health = hp; this.damage = dmg; this.speed = speed; return this; }
        Props armor(double armor) { this.armor = armor; return this; }
        Props attack(AttackStyle a) { this.attack = a; return this; }
        Props diet(Diet d) { this.diet = d; return this; }
        Props treat(Supplier<Item> t) { this.treat = t; return this; }
        Props color(int c) { this.color = c; return this; }
        Props fireImmune() { this.fireImmune = true; return this; }
        Props waterBreathing() { this.waterBreathing = true; return this; }
        Props flying() { this.flying = true; return this; }
        Props belly() { this.belly = true; return this; }
        Props names(String... n) { this.names = List.of(n); return this; }
    }
}
