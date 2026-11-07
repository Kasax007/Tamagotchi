package net.kasax.tamacraft.block;

import java.util.EnumMap;
import java.util.Map;
import net.minecraft.core.Direction;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Horizontal rotations of a block shape drawn facing north (1.21.1 has no Shapes.rotateHorizontal). */
public final class ShapeUtil {
    private ShapeUtil() {
    }

    public static Map<Direction, VoxelShape> rotateHorizontal(VoxelShape north) {
        Map<Direction, VoxelShape> out = new EnumMap<>(Direction.class);
        out.put(Direction.NORTH, north);
        out.put(Direction.EAST, rotate(north, 1));
        out.put(Direction.SOUTH, rotate(north, 2));
        out.put(Direction.WEST, rotate(north, 3));
        return out;
    }

    /** Turns the shape clockwise (seen from above) around the block centre, {@code quarters} times 90 degrees. */
    private static VoxelShape rotate(VoxelShape shape, int quarters) {
        VoxelShape out = Shapes.empty();
        for (AABB b : shape.toAabbs()) {
            double x0 = b.minX, z0 = b.minZ, x1 = b.maxX, z1 = b.maxZ;
            for (int i = 0; i < quarters; i++) {
                // clockwise: (x, z) -> (1 - z, x)
                double nx0 = 1 - z1, nx1 = 1 - z0, nz0 = x0, nz1 = x1;
                x0 = nx0;
                x1 = nx1;
                z0 = nz0;
                z1 = nz1;
            }
            out = Shapes.or(out, Shapes.box(x0, b.minY, z0, x1, b.maxY, z1));
        }
        return out.optimize();
    }
}
