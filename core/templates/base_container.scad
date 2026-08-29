// base_container.scad — template agnóstico de lote/terreno para OpenSCAD.
//
// Unidade: centímetros (nativa do Sweet Home 3D). Eixos: X = largura (testada),
// Y = profundidade (frente → fundo), Z = altura.
//
// Uso: `use <.../core/templates/base_container.scad>` e chame `container(...)`.
// Dentro de `%` (modificador de fundo) o container aparece transparente no
// preview e NÃO entra na exportação — só a edificação vira malha.

// Grade de referência no plano do solo.
module grade(largura, profundidade, passo = 100, espessura = 0.5) {
    for (x = [0 : passo : largura])
        translate([x - espessura / 2, 0, 0]) cube([espessura, profundidade, 0.2]);
    for (y = [0 : passo : profundidade])
        translate([0, y - espessura / 2, 0]) cube([largura, espessura, 0.2]);
}

// Seta apontando o norte, girada por `orientacao_norte` (graus, sentido horário a partir de +Y).
module seta_norte(x, y, tamanho = 100, orientacao_norte = 0) {
    translate([x, y, 0]) rotate([0, 0, -orientacao_norte])
        color("red") linear_extrude(height = 1)
            polygon([[0, tamanho], [-tamanho / 4, 0], [0, tamanho / 6], [tamanho / 4, 0]]);
}

// O container: solo + envelope construível (área que sobra após os recuos).
module container(
    largura, profundidade,
    recuo_frente = 0, recuo_fundo = 0, recuo_lateral = 0,
    orientacao_norte = 0, declividade = 0,
    espessura_solo = 20, mostrar_grade = true
) {
    // Solo: laje fina abaixo de z = 0, inclinada pela declividade (% ao longo de Y).
    desnivel = profundidade * declividade / 100;
    color("darkseagreen")
        multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, desnivel / profundidade, 1, -espessura_solo], [0, 0, 0, 1]])
            cube([largura, profundidade, espessura_solo]);

    // Envelope construível (recuos descontados): parede fina, transparente por estar no `%`.
    translate([recuo_lateral, recuo_frente, 0])
        color("steelblue", 0.25)
            cube([largura - 2 * recuo_lateral, profundidade - recuo_frente - recuo_fundo, 1]);

    if (mostrar_grade) color("gray", 0.4) grade(largura, profundidade);
    seta_norte(largura + 150, profundidade / 2, orientacao_norte = orientacao_norte);
}
