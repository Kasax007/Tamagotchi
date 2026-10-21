package net.kasax.tamagotchi.mixin;

import net.kasax.tamagotchi.world.PetSpawns;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** After a structure is placed in a chunk, maybe put its pet there. */
@Mixin(StructureStart.class)
public abstract class StructureStartMixin {
    @Shadow
    @Final
    private Structure structure;

    @Inject(method = "placeInChunk", at = @At("TAIL"))
    private void tamagotchi$spawnPet(WorldGenLevel level, StructureManager structureManager, ChunkGenerator generator, RandomSource random,
                                     BoundingBox chunkBB, ChunkPos chunkPos, CallbackInfo ci) {
        PetSpawns.afterPlace(level, this.structure, ((StructureStart) (Object) this).getPieces(), chunkBB, chunkPos);
    }
}
