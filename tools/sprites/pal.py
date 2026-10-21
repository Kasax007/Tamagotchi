"""Named palette ramps: [highlight, light, base, shadow, deep].

Most ramps come from ``auto_ramp`` (OKLab lightness steps, highlights drift warm, shadows drift cool and
saturate a little); a few are written out by hand where the generated ramp needed a nudge.
Everything is registered in ``pxl.RAMPS`` so map legends can refer to them by name.
"""
from pxl import define, RAMPS, hex2rgb, rgb2hex, auto_ramp

# ---- shared materials -------------------------------------------------------------------
define("coral", ["#FFA08A", "#F4705F", "#DC4C52", "#B73A4E", "#862C47"])        # bed rim, ball, bits of red
define("cream", ["#FFF8E4", "#FBEBC8", "#F0D6A6", "#D6B592", "#B08F7C"])        # cushion, stem, plaque
define("wicker", ["#F6D58E", "#E3B565", "#C99350", "#A06C3C", "#744829"])         # basket weave
define("wicker_gap", ["#8A5A32", "#6C4527", "#54351F", "#3E2717", "#2A1A10"])     # dark gaps in weave
define("blue_check", ["#8BB6F2", "#5F96E6", "#4678CE", "#3558A8", "#273E7E"])     # blanket blue
define("blanket_white", ["#FFFCF4", "#F4F0EA", "#E1DFE6", "#C5C7DA", "#A3A8C6"])  # blanket white (cool shadows)
define("straw", ["#FBE9A0", "#EFCB6C", "#D8A74A", "#B07D36", "#80552A"])          # nest straw
define("twig", ["#B98355", "#93633C", "#6E4A2E", "#503622", "#37251A"])           # nest twigs
define("down", ["#FFFDF8", "#FBF3EA", "#EDE3E6", "#D3CCDC", "#B3AECB"])           # soft down feathers
define("shell", ["#FFFBEF", "#F8EBD2", "#EAD3B1", "#CDAE98", "#A98C86"])          # eggshell
define("gold", ["#FFF4A8", "#FFDB52", "#F4B636", "#C98024", "#8F5320"])           # coin, rim, crown
define("ceramic", ["#EAF8FF", "#BFE5F8", "#8FCBEF", "#639FD6", "#4575B0"])        # light-blue bowl
define("kibble", ["#C68E58", "#A56E3F", "#855030", "#623822", "#452516"])         # brown kibble
define("tubwood", ["#DDAE70", "#C28B4D", "#A06A3A", "#7C4C2B", "#58341F"])        # tub staves
define("iron", ["#CAD3E0", "#9AA6BA", "#707E96", "#4D5972", "#343C52"])           # hoops
define("duck", ["#FFF8B0", "#FFE45E", "#FFC53A", "#EE9A2C", "#B96520"])           # rubber duck
define("beak", ["#FFC070", "#FF9C3C", "#F27A2A", "#C85626", "#8E3A22"])
define("water", ["#D7F7FF", "#90E0F7", "#53BEEE", "#3294DA", "#2468B2"])           # bath water
define("foam", ["#FFFFFF", "#F0FCFF", "#D5F2FC", "#A9DDF3", "#7DBDE6"])            # soap bubbles (white allowed in a highlight)
define("cap", ["#FF8C80", "#EE5A4C", "#D63C45", "#AE2C47", "#7C2142"])             # mushroom cap
define("spot", ["#FFFCF2", "#FBEFE0", "#EBD6CC", "#CFB4B8", "#AA919F"])            # mushroom spots
define("lightwood", ["#F6DFA6", "#E6C17E", "#CD9D5C", "#A5753F", "#78502E"])        # running wheel stand
define("copper", ["#FFD2A6", "#F6A272", "#D8744C", "#A8503F", "#6E3333"])           # copper bits
define("carpet", ["#CDBBF2", "#AE98E6", "#8E78D0", "#6F5AB0", "#524088"])           # lilac carpet
define("sisal", ["#F2DBA6", "#DDBE82", "#C29D62", "#9A7545", "#6E5033"])            # rope
define("pompom", ["#FFD0E2", "#FF9CC2", "#F0689F", "#C24480", "#8C2F63"])
define("housewood", ["#EBC48A", "#D6A065", "#B87C46", "#8F5C35", "#693F29"])        # dog-house planks
define("shingle", ["#F28068", "#D9544C", "#B83C46", "#8E2B42", "#661F3C"])          # red roof

# ---- item materials ---------------------------------------------------------------------
define("heartpink", ["#FFC4D2", "#FF8FA8", "#F0506F", "#C22E5C", "#8A1F4D"])
define("shellpink", ["#FFE6EE", "#FFCADB", "#F7A8C4", "#D883A8", "#AA6590"])        # pager shell
define("lcd", ["#E4F8B8", "#BEE87E", "#8FC85A", "#5E9A44", "#2F5A33"])              # LCD greens
define("woodbrush", ["#D6A06A", "#B97E48", "#946034", "#6E4528", "#4C2E1C"])
define("steel", ["#F0F4FA", "#C7D2E4", "#9AA9C4", "#6E7FA3", "#485678"])             # laser pen silver
define("laserblue", ["#9CC4FF", "#6B9CF0", "#4772D2", "#3253A8", "#233A7C"])
define("laserred", ["#FFC0B8", "#FF7468", "#F03A3E", "#BC2438", "#80192F"])
define("ballred", ["#FF9A86", "#F4604F", "#DB3C46", "#B02A44", "#80203F"])
define("ballyellow", ["#FFF4A0", "#FFDE52", "#FFC03A", "#E89A2C", "#B26822"])
define("featherpink", ["#FFD2E2", "#FF9FC0", "#F46C9E", "#C84880", "#8F3066"])
define("featheryellow", ["#FFF6B8", "#FFE56A", "#FFC83E", "#E29E2E", "#A8692A"])
define("featherteal", ["#B8F6EA", "#6DE3D0", "#32BFB4", "#1F928F", "#16686E"])
define("string", ["#FFFFFF", "#F4EEE2", "#DBD2C4", "#B8AA9C", "#8A7C74"])
define("sack", ["#CFE8FF", "#8CBBF2", "#5B90DC", "#4069B6", "#2C4A8A"])              # kibble sack (blue, so the white paw pops)
define("fishcracker", ["#FFE08A", "#FFBE4E", "#F29A38", "#C9702B", "#8E4A26"])
define("pitaya", ["#FF8FC6", "#F2509F", "#D52E85", "#A41E70", "#701A5E"])             # dragon fruit skin
define("pitaya_leaf", ["#C8F28A", "#7CD05A", "#44A845", "#2E7C3C", "#1F5634"])
define("pitaya_flesh", ["#FFFFFF", "#FBF6F1", "#EEE8EC", "#D6CFDC", "#B2ADC6"])
define("jerky", ["#E0645A", "#B8413F", "#8C2E36", "#661F31", "#45152A"])
define("ember", ["#FFF2A0", "#FFD24A", "#FF9A2E", "#F0601E", "#B8341F"])
define("crystal_purple", ["#F1E2FF", "#CDA6F6", "#A070E4", "#7C4DC4", "#5A339A"])
define("crystal_pink", ["#FFE6F2", "#FFB4D8", "#F27CB8", "#CC4F96", "#9A3578"])
define("crystal_aqua", ["#E2FFFA", "#9CF0E2", "#52D2CC", "#2DA2B4", "#1E7592"])
define("gummy", ["#F6FFB0", "#D6F85E", "#A8E83A", "#72C42E", "#44962C"])
define("biscuit", ["#FFF0A6", "#FFD95A", "#F2B238", "#C98424", "#8F5A22"])
define("ink", ["#5B4F74", "#46405F", "#34304D", "#262540", "#1B1B33"])              # dark outlines for bubbles etc.

if __name__ == "__main__":
    for k, v in RAMPS.items():
        print(f"{k:16s}", " ".join(rgb2hex(c) for c in v))
