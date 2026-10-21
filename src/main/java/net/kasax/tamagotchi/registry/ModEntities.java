package net.kasax.tamagotchi.registry;

import java.util.EnumMap;
import java.util.IdentityHashMap;
import java.util.Map;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.kasax.tamagotchi.pet.TamaPet;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;

/** One entity type per species, all built on {@link TamaPet}. */
public final class ModEntities {
    public static final Map<PetSpecies, EntityType<TamaPet>> TYPES = new EnumMap<>(PetSpecies.class);
    private static final Map<EntityType<?>, PetSpecies> SPECIES = new IdentityHashMap<>();

    static {
        for (PetSpecies s : PetSpecies.values()) {
            ResourceKey<EntityType<?>> key = ResourceKey.create(Registries.ENTITY_TYPE, s.key());
            EntityType.Builder<TamaPet> b = EntityType.Builder.<TamaPet>of(TamaPet::new, MobCategory.CREATURE)
                    .sized(s.width(), s.height())
                    .eyeHeight(s.height() * 0.75F)
                    .clientTrackingRange(10);
            if (s.fireImmune()) {
                b = b.fireImmune();
            }
            EntityType<TamaPet> type = b.build(key);
            TYPES.put(s, type);
            SPECIES.put(type, s);
        }
    }

    private ModEntities() {
    }

    public static PetSpecies speciesOf(EntityType<?> type) {
        PetSpecies s = SPECIES.get(type);
        return s != null ? s : PetSpecies.DESERT_DRAGON;
    }

    public static EntityType<TamaPet> type(PetSpecies s) {
        return TYPES.get(s);
    }

    public static void initialize() {
        for (PetSpecies s : PetSpecies.values()) {
            Registry.register(BuiltInRegistries.ENTITY_TYPE, ResourceKey.create(Registries.ENTITY_TYPE, s.key()), TYPES.get(s));
            FabricDefaultAttributeRegistry.register(TYPES.get(s), TamaPet.createAttributes(s));
        }
    }
}
