package net.kasax.tamacraft;

import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Until 1.2.0 this mod was called Tamagotchi: every id lived in the namespace {@code tamagotchi} (and the heart was
 * {@code tamagotchi:tamagotchi_heart}). Worlds, inventories, chests, pets, block entities, advancements, recipe books,
 * data packs and modpack files from then still name them. {@link net.kasax.tamacraft.mixin.LegacyIdMixin} sends every
 * id that is parsed or built with the old namespace here, so it reads as the new one; nothing in the game keeps the
 * old name.
 */
public final class LegacyIds {
    public static final String OLD_NAMESPACE = "tamagotchi";
    private static final AtomicBoolean LOGGED = new AtomicBoolean();

    private LegacyIds() {
    }

    public static boolean isOld(String namespace) {
        return OLD_NAMESPACE.equals(namespace);
    }

    /** The new path of an old one: only the word itself changes ({@code tamagotchi_heart} becomes {@code tamacraft_heart}). */
    public static String path(String path) {
        return path.contains(OLD_NAMESPACE) ? path.replace(OLD_NAMESPACE, Tamacraft.MOD_ID) : path;
    }

    /** Called whenever an old id is turned into a new one; tells the log once. */
    public static void used(String namespace, String path) {
        if (LOGGED.compareAndSet(false, true)) {
            Tamacraft.LOGGER.info("Reading ids from before the rename ({}:{} and the like) as {}:...", namespace, path, Tamacraft.MOD_ID);
        }
    }
}
