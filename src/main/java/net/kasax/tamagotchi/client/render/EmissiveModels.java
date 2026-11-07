package net.kasax.tamagotchi.client.render;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.fabricmc.fabric.api.client.model.loading.v1.ModelLoadingPlugin;
import net.fabricmc.fabric.api.renderer.v1.RendererAccess;
import net.fabricmc.fabric.api.renderer.v1.mesh.MutableQuadView;
import net.fabricmc.fabric.api.renderer.v1.model.ForwardingBakedModel;
import net.fabricmc.fabric.api.renderer.v1.render.RenderContext;
import net.kasax.tamagotchi.Tamagotchi;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.BlockAndTintGetter;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;

/**
 * Glowing model parts: the lit egg lamp, the warm incubator, the pager's screen and the laser's tip. 26.x reads
 * "light_emission" on model elements; 1.21.1 ignores it, so the elements that have it are drawn emissive through the
 * Fabric renderer API (the boxes come from the same model files).
 */
@Environment(EnvType.CLIENT)
public final class EmissiveModels {
    private static final List<String> MODELS = List.of("block/egg_lamp_lit", "block/pet_incubator_on", "item/tama_pager_3d", "item/laser_pointer_3d");

    private EmissiveModels() {
    }

    public static void register() {
        if (!RendererAccess.INSTANCE.hasRenderer()) {
            return;
        }
        Map<ResourceLocation, List<AABB>> boxes = new java.util.HashMap<>();
        for (String m : MODELS) {
            List<AABB> b = emissiveBoxes(m);
            if (!b.isEmpty()) {
                boxes.put(Tamagotchi.id(m), b);
            }
        }
        ModelLoadingPlugin.register(ctx -> ctx.modifyModelAfterBake().register((model, c) -> {
            List<AABB> b = c.resourceId() == null ? null : boxes.get(c.resourceId());
            return b == null || model == null ? model : new Glow(model, rotated(b, c.settings().getRotation().getMatrix()));
        }));
    }

    /** The elements with "light_emission" in a model file of the mod, in block units (slightly grown). */
    private static List<AABB> emissiveBoxes(String model) {
        List<AABB> out = new ArrayList<>();
        try (InputStream in = EmissiveModels.class.getResourceAsStream("/assets/tamagotchi/models/" + model + ".json")) {
            if (in == null) {
                return out;
            }
            JsonObject root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
            for (JsonElement e : root.getAsJsonArray("elements")) {
                JsonObject el = e.getAsJsonObject();
                if (!el.has("light_emission") || el.get("light_emission").getAsInt() <= 0) {
                    continue;
                }
                JsonArray f = el.getAsJsonArray("from"), t = el.getAsJsonArray("to");
                out.add(new AABB(f.get(0).getAsDouble() / 16, f.get(1).getAsDouble() / 16, f.get(2).getAsDouble() / 16,
                        t.get(0).getAsDouble() / 16, t.get(1).getAsDouble() / 16, t.get(2).getAsDouble() / 16).inflate(0.002));
            }
        } catch (Exception e) {
            Tamagotchi.LOGGER.warn("Could not read the glowing parts of {}", model, e);
        }
        return out;
    }

    /** The boxes turned like the blockstate variant turns the model (around the block centre). */
    private static List<AABB> rotated(List<AABB> boxes, org.joml.Matrix4f m) {
        List<AABB> out = new ArrayList<>();
        for (AABB b : boxes) {
            double[] lo = {Double.MAX_VALUE, Double.MAX_VALUE, Double.MAX_VALUE}, hi = {-Double.MAX_VALUE, -Double.MAX_VALUE, -Double.MAX_VALUE};
            for (int c = 0; c < 8; c++) {
                org.joml.Vector4f p = new org.joml.Vector4f((float) ((c & 1) == 0 ? b.minX : b.maxX) - 0.5F,
                        (float) ((c & 2) == 0 ? b.minY : b.maxY) - 0.5F, (float) ((c & 4) == 0 ? b.minZ : b.maxZ) - 0.5F, 1F);
                m.transform(p);
                double[] v = {p.x + 0.5, p.y + 0.5, p.z + 0.5};
                for (int i = 0; i < 3; i++) {
                    lo[i] = Math.min(lo[i], v[i]);
                    hi[i] = Math.max(hi[i], v[i]);
                }
            }
            out.add(new AABB(lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]));
        }
        return out;
    }

    private static final class Glow extends ForwardingBakedModel {
        private final List<AABB> boxes;
        private final RenderContext.QuadTransform transform;

        Glow(BakedModel wrapped, List<AABB> boxes) {
            this.wrapped = wrapped;
            this.boxes = boxes;
            this.transform = this::mark;
        }

        private boolean mark(MutableQuadView quad) {
            for (AABB b : this.boxes) {
                boolean inside = true;
                for (int v = 0; v < 4 && inside; v++) {
                    inside = b.contains(quad.x(v), quad.y(v), quad.z(v));
                }
                if (inside) {
                    quad.material(RendererAccess.INSTANCE.getRenderer().materialFinder().copyFrom(quad.material()).emissive(true).find());
                    break;
                }
            }
            return true;
        }

        @Override
        public boolean isVanillaAdapter() {
            return false;
        }

        @Override
        public void emitBlockQuads(BlockAndTintGetter level, BlockState state, BlockPos pos, Supplier<RandomSource> random, RenderContext context) {
            context.pushTransform(this.transform);
            super.emitBlockQuads(level, state, pos, random, context);
            context.popTransform();
        }

        @Override
        public void emitItemQuads(ItemStack stack, Supplier<RandomSource> random, RenderContext context) {
            context.pushTransform(this.transform);
            super.emitItemQuads(stack, random, context);
            context.popTransform();
        }
    }
}
