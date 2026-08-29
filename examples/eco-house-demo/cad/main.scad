// main.scad — junta o terreno (container, transparente) e a casa (sólido).
//
// Fluxo: data/*.yaml → `arch-engine scad-params` → cad/gen/params.scad → aqui.
// Sem o arquivo gerado, os defaults abaixo valem e o modelo abre sozinho.
// Exportar (só a casa entra na malha, porque o terreno está no `%`):
//   openscad -o render/modelo.off main.scad
//   openscad -o render/modelo.png --render --viewall --autocenter main.scad

include <casa.scad>
include <terreno.scad>
include <gen/params.scad>   // gerado; ausência só emite um aviso

function ou(valor, padrao) = is_undef(valor) ? padrao : valor;

// Edificação (independente do terreno)
L  = ou(edificacao_largura, 900);
P  = ou(edificacao_profundidade, 1200);
H  = ou(edificacao_pe_direito, 300);
E  = ou(edificacao_espessura_parede, 30);
I  = ou(edificacao_inclinacao_cobertura, 20);

// Lote (container) — mude à vontade: a casa não muda, só a implantação.
LL = ou(lote_largura, 1500);
LP = ou(lote_profundidade, 3000);
RF = ou(lote_recuo_frente, 500);
RD = ou(lote_recuo_fundo, 300);
RL = ou(lote_recuo_lateral, 150);
ON = ou(lote_orientacao_norte, 0);
DC = ou(lote_declividade, 3);

%terreno(LL, LP, recuo_frente = RF, recuo_fundo = RD, recuo_lateral = RL,
         orientacao_norte = ON, declividade = DC);

translate([RL, RF, 0])
    casa(L, P, H, espessura = E, inclinacao = I);
