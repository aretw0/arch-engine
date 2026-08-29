// casa.scad — módulo paramétrico da edificação (centímetros).
//
// A integridade matemática da casa depende só dos seus próprios parâmetros:
// paredes = caixa externa − caixa interna; cobertura = prisma de duas águas
// cuja cumeeira sai de largura/2 × tan(inclinação). Nada aqui lê o terreno.

module casa(
    largura = 900, profundidade = 1200, pe_direito = 300,
    espessura = 30, inclinacao = 20,
    porta = [90, 210], // largura × altura da porta na fachada frontal
    cor_parede = "burlywood", cor_telhado = "firebrick"
) {
    // Paredes externas com vão de porta na frente (y = 0).
    color(cor_parede) difference() {
        cube([largura, profundidade, pe_direito]);
        translate([espessura, espessura, -1])
            cube([largura - 2 * espessura, profundidade - 2 * espessura, pe_direito + 2]);
        translate([largura / 2 - porta[0] / 2, -1, -1])
            cube([porta[0], espessura + 2, porta[1] + 1]);
    }

    // Cobertura de duas águas: triângulo no plano XZ extrudido ao longo de Y.
    cumeeira = (largura / 2) * tan(inclinacao);
    color(cor_telhado) translate([0, 0, pe_direito])
        rotate([90, 0, 0]) translate([0, 0, -profundidade])
            linear_extrude(height = profundidade)
                polygon([[0, 0], [largura, 0], [largura / 2, cumeeira]]);
}
