package net.kasax.tamagotchi.client.screen;

import com.mojang.blaze3d.platform.InputConstants;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.kasax.tamagotchi.pet.TamaPet;
import net.kasax.tamagotchi.registry.ModBlocks;
import net.kasax.tamagotchi.registry.ModEntities;
import net.kasax.tamagotchi.registry.ModItems;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/**
 * The Tamacon: a pink handheld with an LCD that explains everything about the pets. A contents page links to
 * chapters; chapter text comes from the language file ({@code tamacon.tamagotchi.<id>}) and is paged to fit.
 */
@Environment(EnvType.CLIENT)
public class TamaconScreen extends Screen {
    private static final int W = 240, H = 186;
    private static final int SHELL = 0xFFF4AFC8, SHELL_DARK = 0xFFC86E92, SHELL_LIGHT = 0xFFFFD6E5;
    private static final int LCD = 0xFFC3D69E, LCD_DARK = 0xFF2E3A21, LCD_MID = 0xFF5F7445, LCD_SHADE = 0xFFAEC388, LCD_HOVER = 0xFFB2C98A;
    private static final int LX = 10, LY = 10, LW = W - 20, LH = H - 42;
    private static final int PORTRAIT = 64;

    /** A chapter: its id, the item icons shown under the title, or the pet whose portrait is shown. */
    private record Chapter(String id, List<ItemStack> icons, PetSpecies pet) {
        Component title() {
            return Component.translatable("tamacon.tamagotchi." + id + ".title");
        }
    }

    private record Page(Chapter chapter, List<FormattedCharSequence> lines, boolean first) {
    }

    private static int lastPage;

    private final List<Chapter> chapters = new ArrayList<>();
    private final List<Page> pages = new ArrayList<>();
    private final List<Integer> chapterStart = new ArrayList<>();
    private final Map<PetSpecies, TamaPet> dummies = new EnumMap<>(PetSpecies.class);
    private int page;
    private int left;
    private int top;
    private Button prev;
    private Button next;

    public TamaconScreen() {
        super(Component.translatable("item.tamagotchi.tamacon"));
        add("welcome", List.of(new ItemStack(ModItems.TAMACON), new ItemStack(ModItems.TAMAGOTCHI_HEART)));
        add("finding", List.of(new ItemStack(ModItems.TAMAGOTCHI_HEART), new ItemStack(Items.SANDSTONE), new ItemStack(Items.MOSSY_COBBLESTONE),
                new ItemStack(Items.PRISMARINE), new ItemStack(Items.SNOW_BLOCK), new ItemStack(Items.NETHER_BRICKS)));
        add("controls", List.of(new ItemStack(Items.CHEST), new ItemStack(Items.SHEARS), new ItemStack(ModItems.TAMA_PAGER),
                new ItemStack(Items.LEAD), new ItemStack(Items.NAME_TAG)));
        add("care", List.of(new ItemStack(ModItems.PET_KIBBLE), new ItemStack(ModItems.SQUEAKY_BALL), new ItemStack(ModBlocks.PET_BED),
                new ItemStack(ModItems.PET_BRUSH)));
        add("pager", List.of(new ItemStack(ModItems.TAMA_PAGER)));
        add("backpack", List.of(new ItemStack(Items.CHEST), new ItemStack(Items.GOLDEN_APPLE), new ItemStack(Items.SHEARS)));
        add("combat", List.of(new ItemStack(Items.IRON_SWORD), new ItemStack(ModItems.TAMA_EGG)));
        add("flying", List.of(new ItemStack(Items.FEATHER), new ItemStack(Items.PHANTOM_MEMBRANE)));
        for (PetSpecies s : PetSpecies.values()) {
            this.chapters.add(new Chapter(s.id(), List.of(), s));
        }
        add("food", List.of(new ItemStack(ModItems.PET_KIBBLE), new ItemStack(ModItems.FISH_CRACKERS), new ItemStack(ModItems.DRAGON_FRUIT),
                new ItemStack(ModItems.EMBER_JERKY), new ItemStack(ModItems.ROCK_CANDY), new ItemStack(ModItems.GLOW_GUMMY),
                new ItemStack(ModItems.GOLDEN_BISCUIT)));
        add("toys", List.of(new ItemStack(ModItems.LASER_POINTER), new ItemStack(ModItems.SQUEAKY_BALL), new ItemStack(ModItems.FEATHER_WAND),
                new ItemStack(ModItems.PET_BRUSH)));
        add("furniture", List.of(new ItemStack(ModBlocks.PET_BED), new ItemStack(ModBlocks.PET_BASKET), new ItemStack(ModBlocks.DRAGON_NEST),
                new ItemStack(ModBlocks.FOOD_BOWL), new ItemStack(ModBlocks.PET_BATH), new ItemStack(ModBlocks.BOUNCY_MUSHROOM),
                new ItemStack(ModBlocks.RUNNING_WHEEL), new ItemStack(ModBlocks.SCRATCHING_POST), new ItemStack(ModBlocks.PET_HOUSE)));
        add("reactions", List.of(new ItemStack(Items.JUKEBOX), new ItemStack(Items.NOTE_BLOCK), new ItemStack(Items.CAMPFIRE),
                new ItemStack(Items.CAKE), new ItemStack(Items.POPPY), new ItemStack(Items.BELL)));
    }

    private void add(String id, List<ItemStack> icons) {
        this.chapters.add(new Chapter(id, icons, null));
    }

    @Override
    protected void init() {
        this.left = (this.width - W) / 2;
        this.top = (this.height - H) / 2;
        paginate();
        int by = this.top + H - 26;
        this.prev = addRenderableWidget(Button.builder(Component.literal("<"), b -> turn(this.page - 1)).bounds(this.left + 12, by, 30, 18).build());
        addRenderableWidget(Button.builder(Component.translatable("gui.tamagotchi.tamacon.contents"), b -> turn(0))
                .bounds(this.left + W / 2 - 40, by, 80, 18).build());
        this.next = addRenderableWidget(Button.builder(Component.literal(">"), b -> turn(this.page + 1)).bounds(this.left + W - 42, by, 30, 18).build());
        turn(Math.min(lastPage, this.pages.size()));
    }

    /** Page 0 is the contents; every chapter's text is wrapped and split into LCD-sized pages. */
    private void paginate() {
        this.pages.clear();
        this.chapterStart.clear();
        int lineH = this.font.lineHeight + 1;
        for (Chapter c : this.chapters) {
            this.chapterStart.add(this.pages.size() + 1);
            String text = Component.translatable("tamacon.tamagotchi." + c.id()).getString();
            boolean first = true;
            List<FormattedCharSequence> lines = new ArrayList<>();
            int header = c.icons().isEmpty() ? 16 : 36;
            int width = LW - 12 - (c.pet() != null ? PORTRAIT + 4 : 0);
            int capacity = (LH - header - 16) / lineH;   // keep the bottom line free for the page number
            for (String para : text.split("\n")) {
                List<FormattedCharSequence> wrapped = para.isEmpty() ? List.of(FormattedCharSequence.EMPTY)
                        : this.font.split(Component.literal(para), width);
                for (FormattedCharSequence line : wrapped) {
                    if (lines.size() >= capacity) {
                        this.pages.add(new Page(c, lines, first));
                        lines = new ArrayList<>();
                        first = false;
                        header = 16;
                        capacity = (LH - header - 16) / lineH;
                    }
                    lines.add(line);
                }
            }
            if (!lines.isEmpty()) {
                this.pages.add(new Page(c, lines, first));
            }
        }
    }

    private void turn(int to) {
        int max = this.pages.size();
        int p = Math.max(0, Math.min(max, to));
        if (p != this.page && this.minecraft != null) {
            this.minecraft.getSoundManager().play(net.minecraft.client.resources.sounds.SimpleSoundInstance.forUI(SoundEvents.BOOK_PAGE_TURN, 1.2F));
        }
        this.page = p;
        lastPage = p;
        if (this.prev != null) {
            this.prev.active = p > 0;
            this.next.active = p < max;
        }
    }

    @Override
    public boolean keyPressed(KeyEvent event) {
        if (event.key() == InputConstants.KEY_RIGHT || event.key() == InputConstants.KEY_D) {
            turn(this.page + 1);
            return true;
        }
        if (event.key() == InputConstants.KEY_LEFT || event.key() == InputConstants.KEY_A) {
            turn(this.page - 1);
            return true;
        }
        return super.keyPressed(event);
    }

    @Override
    public boolean mouseScrolled(double x, double y, double scrollX, double scrollY) {
        turn(this.page + (scrollY < 0 ? 1 : -1));
        return true;
    }

    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
        if (this.page == 0) {
            int hit = contentsEntryAt(event.x(), event.y());
            if (hit >= 0) {
                turn(this.chapterStart.get(hit));
                return true;
            }
        }
        return super.mouseClicked(event, doubleClick);
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }

    @Override
    public void tick() {
        for (TamaPet pet : this.dummies.values()) {
            pet.tickCount++;
        }
    }

    // ------------------------------------------------------------------ drawing

    @Override
    public void extractBackground(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        super.extractBackground(g, mouseX, mouseY, a);
        int x = this.left, y = this.top;
        PetScreen.roundRect(g, x, y, W, H, SHELL_DARK);
        PetScreen.roundRect(g, x + 1, y + 1, W - 2, H - 2, SHELL);
        g.fill(x + 3, y + 2, x + W - 3, y + 3, SHELL_LIGHT);
        g.fill(x + 2, y + 3, x + 3, y + H - 3, SHELL_LIGHT);
        int lx = x + LX, ly = y + LY;
        g.fill(lx - 2, ly - 2, lx + LW + 2, ly + LH + 2, SHELL_DARK);
        g.fill(lx, ly, lx + LW, ly + LH, LCD);
        g.fill(lx, ly, lx + LW, ly + 1, LCD_SHADE);
        g.fill(lx, ly, lx + 1, ly + LH, LCD_SHADE);
        // three little hearts on the shell, like the buttons of a virtual pet
        for (int i = 0; i < 3; i++) {
            g.fill(x + W / 2 - 14 + i * 12, y + H - 6, x + W / 2 - 10 + i * 12, y + H - 4, SHELL_DARK);
        }
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        super.extractRenderState(g, mouseX, mouseY, a);
        int lx = this.left + LX + 6, ly = this.top + LY + 5;
        if (this.page == 0) {
            drawContents(g, lx, ly, mouseX, mouseY);
        } else {
            drawPage(g, this.pages.get(this.page - 1), lx, ly);
        }
        String num = this.page + " / " + this.pages.size();
        g.text(this.font, num, this.left + LX + LW - 4 - this.font.width(num), this.top + LY + LH - 11, LCD_MID, false);
    }

    private void drawContents(GuiGraphicsExtractor g, int lx, int ly, int mouseX, int mouseY) {
        g.text(this.font, Component.translatable("gui.tamagotchi.tamacon.contents"), lx, ly, LCD_DARK, false);
        int hover = contentsEntryAt(mouseX, mouseY);
        for (int i = 0; i < this.chapters.size(); i++) {
            int[] r = contentsRect(i);
            if (i == hover) {
                g.fill(r[0] - 1, r[1] - 1, r[0] + r[2], r[1] + r[3] - 1, LCD_HOVER);
            }
            g.text(this.font, this.chapters.get(i).title(), r[0] + 1, r[1], i == hover ? LCD_DARK : LCD_MID, false);
        }
    }

    /** x, y, w, h of a contents entry: two columns, the pets in the right one. */
    private int[] contentsRect(int i) {
        int lx = this.left + LX + 6, ly = this.top + LY + 18;
        int perCol = (this.chapters.size() + 1) / 2;
        int col = i / perCol, row = i % perCol;
        int colW = (LW - 12) / 2;
        return new int[]{lx + col * colW, ly + row * 10, colW - 4, 10};
    }

    private int contentsEntryAt(double mx, double my) {
        for (int i = 0; i < this.chapters.size(); i++) {
            int[] r = contentsRect(i);
            if (mx >= r[0] && mx < r[0] + r[2] && my >= r[1] - 1 && my < r[1] + r[3] - 1) {
                return i;
            }
        }
        return -1;
    }

    private void drawPage(GuiGraphicsExtractor g, Page p, int lx, int ly) {
        Chapter c = p.chapter();
        g.text(this.font, c.title(), lx, ly, LCD_DARK, false);
        g.fill(lx, ly + 10, this.left + LX + LW - 6, ly + 11, LCD_MID);
        int y = ly + 16;
        if (p.first() && !c.icons().isEmpty()) {
            int ix = lx;
            for (ItemStack icon : c.icons()) {
                g.fill(ix - 1, y - 1, ix + 17, y + 17, LCD_SHADE);
                g.item(icon, ix, y);
                ix += 21;
            }
            y += 20;
        }
        if (c.pet() != null && p.first()) {
            TamaPet pet = dummy(c.pet());
            if (pet != null) {
                int px = this.left + LX + LW - PORTRAIT - 6, py = ly + 16;
                g.fill(px, py, px + PORTRAIT, py + PORTRAIT, LCD_SHADE);
                int size = (int) (38 / Math.max(pet.getBbHeight(), pet.getBbWidth()));
                InventoryScreen.extractEntityInInventoryFollowsMouse(g, px, py, px + PORTRAIT, py + PORTRAIT, size, 0.0625F,
                        px + PORTRAIT * 0.3F, py + PORTRAIT * 0.45F, pet);
            }
        }
        for (FormattedCharSequence line : p.lines()) {
            g.text(this.font, line, lx, y, LCD_DARK, false);
            y += this.font.lineHeight + 1;
        }
    }

    private TamaPet dummy(PetSpecies s) {
        if (this.minecraft == null || this.minecraft.level == null) {
            return null;
        }
        return this.dummies.computeIfAbsent(s, k -> {
            TamaPet pet = ModEntities.type(k).create(this.minecraft.level, EntitySpawnReason.LOAD);
            if (pet != null) {
                pet.setId(-1000 - k.ordinal());   // never added to the level, but rendering asks for an id
            }
            return pet;
        });
    }
}
