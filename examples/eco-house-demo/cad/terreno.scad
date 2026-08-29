// terreno.scad — o lote da demo, um `container` do core com defaults do lote A.
// Valores reais vêm de data/terrenos/lote_a.yaml via cad/gen/params.scad.
use <../../../core/templates/base_container.scad>

module terreno(
    largura = 1500, profundidade = 3000,
    recuo_frente = 500, recuo_fundo = 300, recuo_lateral = 150,
    orientacao_norte = 0, declividade = 3
) {
    container(
        largura, profundidade,
        recuo_frente = recuo_frente, recuo_fundo = recuo_fundo, recuo_lateral = recuo_lateral,
        orientacao_norte = orientacao_norte, declividade = declividade
    );
}
