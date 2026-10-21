package net.kasax.tamagotchi.pet;

import java.util.function.Predicate;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import org.jspecify.annotations.Nullable;

/** Small helper: nearest block around an entity matching a state test (and optionally a position test). */
public final class BlockSearch {
    private BlockSearch() {
    }

    public static @Nullable BlockPos nearest(Entity e, int r, int v, Predicate<BlockState> test) {
        return nearest(e, r, v, test, p -> true);
    }

    public static @Nullable BlockPos nearest(Entity e, int r, int v, Predicate<BlockState> test, Predicate<BlockPos> posTest) {
        Level level = e.level();
        BlockPos origin = e.blockPosition();
        BlockPos best = null;
        double bestD = Double.MAX_VALUE;
        BlockPos.MutableBlockPos m = new BlockPos.MutableBlockPos();
        for (int dy = -v; dy <= v; dy++) {
            for (int dx = -r; dx <= r; dx++) {
                for (int dz = -r; dz <= r; dz++) {
                    m.set(origin.getX() + dx, origin.getY() + dy, origin.getZ() + dz);
                    double d = dx * dx + dy * dy * 2 + dz * dz;
                    if (d >= bestD || !level.isLoaded(m)) {
                        continue;
                    }
                    if (test.test(level.getBlockState(m)) && posTest.test(m)) {
                        best = m.immutable();
                        bestD = d;
                    }
                }
            }
        }
        return best;
    }
}
