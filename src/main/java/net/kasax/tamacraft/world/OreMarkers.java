package net.kasax.tamacraft.world;

import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.server.ServerStoppedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

import com.mojang.math.Transformation;
import java.util.HashSet;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.level.block.state.BlockState;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * The Pebble Golem's find: a glowing copy of the ore block that shows through walls for a while.
 * Markers carry their expiry time in a tag, so ones saved with the world are cleaned up after a reload too.
 */
public final class OreMarkers {
    private static final String TAG = "tamacraft_ore_marker@";
    /** The tag of markers saved before the rename (1.2.0 and older), so they still expire. */
    private static final String OLD_TAG = "tamagotchi_ore_marker@";
    private static final Set<Display.BlockDisplay> LIVE = new HashSet<>();

    private OreMarkers() {
    }

    public static void initialize() {
        NeoForge.EVENT_BUS.addListener((EntityJoinLevelEvent event) -> {
            if (!event.getLevel().isClientSide() && event.getEntity() instanceof Display.BlockDisplay d && expiry(d) >= 0) {
                LIVE.add(d);
            }
        });
        // the next world in this game must not keep the last one's markers (and with them its level) alive
        NeoForge.EVENT_BUS.addListener((ServerStoppedEvent event) -> LIVE.clear());
        NeoForge.EVENT_BUS.addListener((ServerTickEvent.Post event) -> {
            if (LIVE.isEmpty() || event.getServer().getTickCount() % 20 != 0) {
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
        Display.BlockDisplay d = EntityType.BLOCK_DISPLAY.create(level);
        if (d == null) {
            return;
        }
        d.setBlockState(state);
        d.moveTo(pos.getX(), pos.getY(), pos.getZ(), 0, 0);
        d.setTransformation(new Transformation(new Vector3f(-0.01F), new Quaternionf(), new Vector3f(1.02F), new Quaternionf()));
        d.setGlowingTag(true);
        d.setGlowColorOverride(color);
        d.addTag(TAG + (level.getGameTime() + ticks));
        level.addFreshEntity(d);
    }

    private static long expiry(Entity e) {
        for (String t : e.getTags()) {
            String prefix = t.startsWith(TAG) ? TAG : t.startsWith(OLD_TAG) ? OLD_TAG : null;
            if (prefix != null) {
                try {
                    return Long.parseLong(t.substring(prefix.length()));
                } catch (NumberFormatException ignored) {
                    return 0;
                }
            }
        }
        return -1;
    }
}
