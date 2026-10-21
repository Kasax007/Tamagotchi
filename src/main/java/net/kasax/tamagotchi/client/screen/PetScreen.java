package net.kasax.tamagotchi.client.screen;

import java.util.List;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.kasax.tamagotchi.Tamagotchi;
import net.kasax.tamagotchi.menu.PetMenu;
import net.kasax.tamagotchi.pet.PetNeeds.Mood;
import net.kasax.tamagotchi.pet.PetNeeds.Need;
import net.kasax.tamagotchi.pet.TamaPet;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.player.Inventory;

/**
 * The pet screen, styled like a little virtual-pet device: a pink shell, a green LCD with the
 * pet, its mood, needs, bond and talent, and the backpack slots next to it.
 */
@Environment(EnvType.CLIENT)
public class PetScreen extends AbstractContainerScreen<PetMenu> {
    private static final Identifier ICONS = Tamagotchi.id("textures/gui/pet_icons.png");
    private static final Identifier SLOT = Identifier.withDefaultNamespace("container/slot");

    private static final int SHELL = 0xFFF4AFC8, SHELL_DARK = 0xFFC86E92, SHELL_LIGHT = 0xFFFFD6E5;
    private static final int LCD = 0xFFC3D69E, LCD_DARK = 0xFF2E3A21, LCD_MID = 0xFF7D9160, LCD_SHADE = 0xFFAEC388;
    private static final int PANEL = 0xFFF8EEDD, PANEL_EDGE = 0xFFD7C1A4;

    private final int rows;
    private float mouseX;
    private float mouseY;
    private Button sit;
    private Button follow;
    private Button wander;

    public PetScreen(PetMenu menu, Inventory inventory, Component title) {
        super(menu, inventory, title, PetMenu.SLOT_X + 162 + 8, PetMenu.SLOT_Y + PetMenu.rowsShown(menu.storageSlots()) * 18 + 14 + 76 + 8);
        this.rows = PetMenu.rowsShown(menu.storageSlots());
        this.inventoryLabelX = PetMenu.SLOT_X;
        this.inventoryLabelY = PetMenu.SLOT_Y + this.rows * 18 + 3;
        this.titleLabelX = PetMenu.SLOT_X;
        this.titleLabelY = 6;
    }

    @Override
    protected void init() {
        super.init();
        int y = this.topPos + this.imageHeight - 26;
        int x = this.leftPos + 7;
        this.sit = addRenderableWidget(Button.builder(Component.translatable("gui.tamagotchi.sit"), b -> press(0)).bounds(x, y, 36, 18).build());
        this.follow = addRenderableWidget(Button.builder(Component.translatable("gui.tamagotchi.follow"), b -> press(1)).bounds(x + 38, y, 38, 18).build());
        this.wander = addRenderableWidget(Button.builder(Component.translatable("gui.tamagotchi.wander"), b -> press(2)).bounds(x + 78, y, 38, 18).build());
    }

    private void press(int id) {
        if (this.minecraft != null && this.minecraft.gameMode != null) {
            this.minecraft.gameMode.handleInventoryButtonClick(this.menu.containerId, id);
        }
    }

    @Override
    protected void containerTick() {
        super.containerTick();
        TamaPet pet = this.menu.pet();
        if (pet != null && this.sit != null) {
            TamaPet.Mode mode = pet.hasFlag(TamaPet.F_WANDER) ? TamaPet.Mode.WANDER
                    : pet.isInSittingPose() ? TamaPet.Mode.SIT : TamaPet.Mode.FOLLOW;
            this.sit.active = mode != TamaPet.Mode.SIT;
            this.follow.active = mode != TamaPet.Mode.FOLLOW;
            this.wander.active = mode != TamaPet.Mode.WANDER;
        }
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        this.mouseX = mouseX;
        this.mouseY = mouseY;
        super.extractRenderState(g, mouseX, mouseY, a);

        talentTooltip(g, mouseX, mouseY);
    }

    @Override
    public void extractBackground(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        super.extractBackground(g, mouseX, mouseY, a);
        int x = this.leftPos;
        int y = this.topPos;
        int w = this.imageWidth;
        int h = this.imageHeight;
        // device shell with rounded corners
        roundRect(g, x, y, w, h, SHELL_DARK);
        roundRect(g, x + 1, y + 1, w - 2, h - 2, SHELL);
        g.fill(x + 3, y + 2, x + w - 3, y + 3, SHELL_LIGHT);
        g.fill(x + 2, y + 3, x + 3, y + h - 3, SHELL_LIGHT);
        // LCD
        int lx = x + 6, ly = y + 6, lw = PetMenu.INFO_W - 8, lh = h - 38;
        g.fill(lx - 1, ly - 1, lx + lw + 1, ly + lh + 1, SHELL_DARK);
        g.fill(lx, ly, lx + lw, ly + lh, LCD);
        g.fill(lx, ly, lx + lw, ly + 1, LCD_SHADE);
        g.fill(lx, ly, lx + 1, ly + lh, LCD_SHADE);
        // slot panel
        int px = x + PetMenu.SLOT_X - 4, py = y + PetMenu.SLOT_Y - 4;
        g.fill(px - 1, y + 3, x + w - 3, y + h - 3, PANEL_EDGE);
        g.fill(px, y + 4, x + w - 4, y + h - 4, PANEL);
        for (int i = 0; i < this.menu.storageSlots(); i++) {
            g.blitSprite(RenderPipelines.GUI_TEXTURED, SLOT, x + PetMenu.SLOT_X - 1 + (i % 9) * 18, y + PetMenu.SLOT_Y - 1 + (i / 9) * 18, 18, 18);
        }
        int invY = y + PetMenu.SLOT_Y + this.rows * 18 + 14;
        for (int r = 0; r < 4; r++) {
            for (int c = 0; c < 9; c++) {
                g.blitSprite(RenderPipelines.GUI_TEXTURED, SLOT, x + PetMenu.SLOT_X - 1 + c * 18, invY - 1 + r * 18 + (r == 3 ? 4 : 0), 18, 18);
            }
        }
        if (this.menu.storageSlots() == 0) {
            int bx = x + PetMenu.SLOT_X, by = y + PetMenu.SLOT_Y + 8;
            g.fill(bx - 1, by - 1, bx + 161, by + 39, PANEL_EDGE);
            g.fill(bx, by, bx + 160, by + 38, 0xFFFFF8EE);
            List<net.minecraft.util.FormattedCharSequence> lines = this.font.split(Component.translatable("gui.tamagotchi.no_backpack"), 150);
            for (int i = 0; i < lines.size() && i < 4; i++) {
                g.text(this.font, lines.get(i), bx + 5, by + 5 + i * 10, 0xFF8A6A4A, false);
            }
        }
        TamaPet pet = this.menu.pet();
        if (pet == null) {
            return;
        }
        // portrait
        InventoryScreen.extractEntityInInventoryFollowsMouse(g, lx + 2, ly + 14, lx + 50, ly + 66, 20, 0.0625F, this.mouseX, this.mouseY, pet);
        lcdInfo(g, pet, lx, ly, lw);
    }

    private void lcdInfo(GuiGraphicsExtractor g, TamaPet pet, int lx, int ly, int lw) {
        g.text(this.font, pet.getName(), lx + 4, ly + 3, LCD_DARK, false);
        // mood face + word
        Mood mood = pet.syncedMood();
        g.blit(RenderPipelines.GUI_TEXTURED, ICONS, lx + 54, ly + 16, mood.ordinal() * 16, 16, 16, 16, 128, 64);
        g.text(this.font, Component.translatable("gui.tamagotchi.mood." + mood.name().toLowerCase(java.util.Locale.ROOT)), lx + 72, ly + 20, LCD_DARK, false);
        // bond hearts (0..100 → 0..5 hearts in halves)
        int bond = pet.syncedBond();
        int halves = Math.round(bond / 10F);
        for (int i = 0; i < 5; i++) {
            int u = halves >= (i + 1) * 2 ? 40 : halves == i * 2 + 1 ? 50 : 60;
            g.blit(RenderPipelines.GUI_TEXTURED, ICONS, lx + 54 + i * 10, ly + 38, u, 0, 9, 9, 128, 64);
        }
        // snack pouch
        g.blit(RenderPipelines.GUI_TEXTURED, ICONS, lx + 54, ly + 51, 70, 0, 9, 9, 128, 64);
        g.text(this.font, "x" + pet.syncedSnacks(), lx + 65, ly + 52, LCD_DARK, false);
        // needs as LCD segment bars
        Need[] needs = Need.values();
        for (int i = 0; i < needs.length; i++) {
            int y = ly + 70 + i * 12;
            g.blit(RenderPipelines.GUI_TEXTURED, ICONS, lx + 4, y, i * 10, 0, 10, 10, 128, 64);
            int value = pet.syncedNeed(needs[i]);
            int lit = Math.round(value / 10F);
            for (int s = 0; s < 10; s++) {
                int sx = lx + 18 + s * 9;
                g.fill(sx, y + 2, sx + 8, y + 8, s < lit ? (value < 25 ? 0xFF8A2A1F : LCD_DARK) : LCD_MID);
            }
        }
        // talent
        int ty = ly + 70 + 4 * 12 + 2;
        if (ty + 18 < ly + this.imageHeight - 38) {
            g.text(this.font, Component.translatable("gui.tamagotchi.talent"), lx + 4, ty, LCD_MID, false);
            g.text(this.font, pet.species().talentName(), lx + 4, ty + 10, LCD_DARK, false);
        }
    }

    private void talentTooltip(GuiGraphicsExtractor g, int mouseX, int mouseY) {
        TamaPet pet = this.menu.pet();
        if (pet == null) {
            return;
        }
        int lx = this.leftPos + 6, ly = this.topPos + 6;
        int ty = ly + 70 + 4 * 12 + 2;
        if (mouseX >= lx && mouseX < lx + PetMenu.INFO_W - 8 && mouseY >= ty && mouseY < ty + 20) {
            g.setTooltipForNextFrame(this.font.split(pet.species().talentDescription(), 180), mouseX, mouseY);
        }
        Need[] needs = Need.values();
        for (int i = 0; i < needs.length; i++) {
            int y = ly + 70 + i * 12;
            if (mouseX >= lx && mouseX < lx + 110 && mouseY >= y && mouseY < y + 10) {
                g.setTooltipForNextFrame(Component.translatable("gui.tamagotchi.need." + needs[i].name().toLowerCase(java.util.Locale.ROOT),
                        pet.syncedNeed(needs[i])), mouseX, mouseY);
            }
        }
    }

    private static void roundRect(GuiGraphicsExtractor g, int x, int y, int w, int h, int color) {
        g.fill(x + 2, y, x + w - 2, y + h, color);
        g.fill(x + 1, y + 1, x + w - 1, y + h - 1, color);
        g.fill(x, y + 2, x + w, y + h - 2, color);
    }

    @Override
    protected void extractLabels(GuiGraphicsExtractor g, int xm, int ym) {
        g.text(this.font, Component.translatable(this.menu.storageSlots() > 0 ? "gui.tamagotchi.backpack" : "gui.tamagotchi.no_backpack_title"),
                this.titleLabelX, this.titleLabelY, 0xFF6B4A3A, false);
        g.text(this.font, this.playerInventoryTitle, this.inventoryLabelX, this.inventoryLabelY, 0xFF6B4A3A, false);
    }
}
