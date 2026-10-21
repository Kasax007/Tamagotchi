package net.kasax.tamagotchi.world;

import com.mojang.math.Transformation;
import java.util.HashSet;
import java.util.Set;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.level.block.state.BlockState;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * The Pebble Golem's find: a glowing copy of the ore block that shows through walls for a while.
 * Markers carry their expiry time in a tag, so ones saved with the world are cleaned up after a reload too.
 */
public final class OreMarkers {
    private static final String TAG = "tamagotchi_ore_marker@";
    private static final Set<Display.BlockDisplay> LIVE = new HashSet<>();

    private OreMarkers() {
    }

    public static void initialize() {
        ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
            if (entity instanceof Display.BlockDisplay d && expiry(d) >= 0) {
                LIVE.add(d);
            }
        });
        ServerTickEvents.END_SERVER_TICK.register(server -> {
            if (LIVE.isEmpty() || server.getTickCount() % 20 != 0) {
                return;
            }
            LIVE.removeIf(d -> {
                if (d.isRemoved()) {
                    return true;
                }
                if (d.level().getGameTime() >= expiry(d)) {
                    d.discard();
                    return true;
                }
                return false;
            });
        });
    }

    public static void mark(ServerLevel level, BlockPos pos, BlockState state, int ticks, int color) {
        Display.BlockDisplay d = EntityTypes.BLOCK_DISPLAY.create(level, EntitySpawnReason.TRIGGERED);
        if (d == null) {
            return;
        }
        d.setBlockState(state);
        d.snapTo(pos.getX(), pos.getY(), pos.getZ(), 0, 0);
        d.setTransformation(new Transformation(new Vector3f(-0.01F), new Quaternionf(), new Vector3f(1.02F), new Quaternionf()));
        d.setGlowingTag(true);
        d.setGlowColorOverride(color);
        d.addTag(TAG + (level.getGameTime() + ticks));
        level.addFreshEntity(d);
    }

    private static long expiry(Entity e) {
        for (String t : e.entityTags()) {
            if (t.startsWith(TAG)) {
                try {
                    return Long.parseLong(t.substring(TAG.length()));
                } catch (NumberFormatException ignored) {
                    return 0;
                }
            }
        }
        return -1;
    }
}
