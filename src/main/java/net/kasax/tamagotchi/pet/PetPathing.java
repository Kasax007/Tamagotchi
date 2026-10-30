package net.kasax.tamagotchi.pet;

import net.kasax.tamagotchi.block.PetFlapBlock;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.ai.navigation.AmphibiousPathNavigation;
import net.minecraft.world.entity.ai.navigation.GroundPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.pathfinder.AmphibiousNodeEvaluator;
import net.minecraft.world.level.pathfinder.PathFinder;
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.level.pathfinder.PathfindingContext;
import net.minecraft.world.level.pathfinder.WalkNodeEvaluator;
import org.jspecify.annotations.Nullable;

/** Pet navigation: the same as vanilla, except that a pet flap is an open doorway to a pet (and a wall to everyone else). */
final class PetPathing {
    private PetPathing() {
    }

    static PathNavigation create(TamaPet pet, Level level, boolean amphibious) {
        if (amphibious) {
            return new AmphibiousPathNavigation(pet, level) {
                @Override
                protected PathFinder createPathFinder(int maxVisitedNodes) {
                    this.nodeEvaluator = new Amphibious();
                    return new PathFinder(this.nodeEvaluator, maxVisitedNodes);
                }
            };
        }
        return new GroundPathNavigation(pet, level) {
            @Override
            protected PathFinder createPathFinder(int maxVisitedNodes) {
                this.nodeEvaluator = new Walk();
                return new PathFinder(this.nodeEvaluator, maxVisitedNodes);
            }
        };
    }

    /** What a flap cell (or the cell right above one) is to a pet; null when there is no flap. */
    private static @Nullable PathType flap(PathfindingContext ctx, int x, int y, int z) {
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos(x, y, z);
        if (ctx.getBlockState(p).getBlock() instanceof PetFlapBlock) {
            return switch (ctx.getPathTypeFromState(x, y - 1, z)) {
                case OPEN, WATER, LAVA -> PathType.OPEN;
                default -> PathType.WALKABLE;
            };
        }
        if (ctx.getBlockState(p.setY(y - 1)).getBlock() instanceof PetFlapBlock) {
            return PathType.OPEN;   // a flap swings, nobody can stand on it
        }
        return null;
    }

    private static final class Walk extends WalkNodeEvaluator {
        @Override
        public PathType getPathType(PathfindingContext ctx, int x, int y, int z) {
            PathType t = flap(ctx, x, y, z);
            return t != null ? t : super.getPathType(ctx, x, y, z);
        }
    }

    private static final class Amphibious extends AmphibiousNodeEvaluator {
        Amphibious() {
            super(false);
        }

        @Override
        public PathType getPathType(PathfindingContext ctx, int x, int y, int z) {
            PathType t = flap(ctx, x, y, z);
            return t != null ? t : super.getPathType(ctx, x, y, z);
        }
    }
}
