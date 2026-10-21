package net.kasax.tamagotchi.world;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import net.kasax.tamagotchi.Tamagotchi;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.kasax.tamagotchi.pet.TamaPet;
import net.kasax.tamagotchi.registry.ModEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.material.Fluids;

/**
 * Pets live in structures: when a structure is generated, one roll decides whether its pet is
 * there. The roll happens in the chunk holding the centre of the first piece, so each structure
 * gets exactly one chance.
 */
public final class PetSpawns {
    public record Rule(PetSpecies species, float chance) {
    }

    public static final Map<Identifier, Rule> RULES = new HashMap<>();

    static {
        rule("desert_pyramid", PetSpecies.DESERT_DRAGON, 0.40F);
        rule("jungle_pyramid", PetSpecies.JUNGLE_DRAGON, 0.40F);
        rule("monument", PetSpecies.TIDE_DRAGON, 0.50F);
        rule("igloo", PetSpecies.FROST_PENGUIN, 0.45F);
        rule("fortress", PetSpecies.EMBER_PUP, 0.30F);
        rule("ancient_city", PetSpecies.SCULK_WISP, 0.50F);
        rule("end_city", PetSpecies.VOID_KITTEN, 0.30F);
        rule("trail_ruins", PetSpecies.PEBBLE_GOLEM, 0.35F);
        rule("mineshaft", PetSpecies.PEBBLE_GOLEM, 0.08F);
        rule("mineshaft_mesa", PetSpecies.PEBBLE_GOLEM, 0.08F);
        rule("swamp_hut", PetSpecies.HEX_TOAD, 0.45F);
        rule("trial_chambers", PetSpecies.MIMIC, 0.30F);
        rule("mansion", PetSpecies.MIMIC, 0.60F);
    }

    private PetSpawns() {
    }

    private static void rule(String structure, PetSpecies species, float chance) {
        RULES.put(Identifier.withDefaultNamespace(structure), new Rule(species, chance));
    }

    public static void afterPlace(WorldGenLevel level, Structure structure, List<StructurePiece> pieces, BoundingBox chunkBB, ChunkPos chunkPos) {
        if (pieces.isEmpty()) {
            return;
        }
        ResourceKey<Structure> key = level.registryAccess().lookupOrThrow(Registries.STRUCTURE).getResourceKey(structure).orElse(null);
        Rule rule = key == null ? null : RULES.get(key.identifier());
        if (rule == null) {
            return;
        }
        BlockPos center = pieces.get(0).getBoundingBox().getCenter();
        if ((center.getX() >> 4) != chunkPos.x() || (center.getZ() >> 4) != chunkPos.z()) {
            return;
        }
        RandomSource rng = RandomSource.create(net.minecraft.world.level.levelgen.RandomSupport.mixStafford13(
                level.getSeed() ^ center.asLong() * 31L ^ key.identifier().hashCode()));
        if (rng.nextFloat() >= rule.chance()) {
            return;
        }
        BlockPos spot = findSpot(level, pieces, chunkBB, rng, rule.species().gait() == PetSpecies.Gait.SWIM);
        if (spot == null) {
            Tamagotchi.LOGGER.debug("No spot for {} in {}", rule.species().id(), key.identifier());
            return;
        }
        TamaPet pet = ModEntities.type(rule.species()).create(level.getLevel(), EntitySpawnReason.STRUCTURE);
        if (pet == null) {
            return;
        }
        pet.snapTo(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5, rng.nextFloat() * 360F, 0);
        pet.setHome(spot);
        pet.finalizeSpawn(level, level.getCurrentDifficultyAt(spot), EntitySpawnReason.STRUCTURE, null);
        level.addFreshEntityWithPassengers(pet);
        Tamagotchi.LOGGER.debug("Spawned a wild {} at {}", rule.species().id(), spot);
    }

    private static BlockPos findSpot(WorldGenLevel level, List<StructurePiece> pieces, BoundingBox chunkBB, RandomSource rng, boolean water) {
        List<BoundingBox> boxes = new ArrayList<>();
        for (StructurePiece p : pieces) {
            BoundingBox b = p.getBoundingBox();
            if (b.intersects(chunkBB)) {
                boxes.add(b);
            }
        }
        if (boxes.isEmpty()) {
            return null;
        }
        for (int attempt = 0; attempt < 120; attempt++) {
            BoundingBox b = boxes.get(rng.nextInt(boxes.size()));
            int x0 = Math.max(b.minX(), chunkBB.minX()), x1 = Math.min(b.maxX(), chunkBB.maxX());
            int z0 = Math.max(b.minZ(), chunkBB.minZ()), z1 = Math.min(b.maxZ(), chunkBB.maxZ());
            if (x0 > x1 || z0 > z1) {
                continue;
            }
            BlockPos p = new BlockPos(x0 + rng.nextInt(x1 - x0 + 1), b.minY() + rng.nextInt(Math.max(1, b.maxY() - b.minY() + 1)), z0 + rng.nextInt(z1 - z0 + 1));
            if (valid(level, p, water)) {
                return p;
            }
        }
        return null;
    }

    private static boolean valid(WorldGenLevel level, BlockPos p, boolean water) {
        BlockState at = level.getBlockState(p);
        BlockState above = level.getBlockState(p.above());
        BlockState below = level.getBlockState(p.below());
        if (!below.isFaceSturdy(level, p.below(), Direction.UP)) {
            return false;
        }
        if (water) {
            return at.getFluidState().is(Fluids.WATER) && above.getFluidState().is(Fluids.WATER)
                    && at.getCollisionShape(level, p).isEmpty();
        }
        return at.isAir() && above.isAir() && below.getFluidState().isEmpty();
    }
}
