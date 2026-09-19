set -e
# Regenerates the diagram figures (1-5, 7, 10). Requires Graphviz (dot).
cd "$(dirname "$0")"
OUT=${1:-../out}
mkdir -p "$OUT"
FONT="DejaVu Sans"
# Fig 1 classification
cat > f1.dot <<G
digraph G { rankdir=LR; nodesep=0.15; ranksep=0.5; bgcolor=white;
 node [shape=box, style="rounded,filled", fontname="$FONT", fontsize=11, fillcolor="#EEF2F7", color="#34495E"];
 edge [color="#34495E", arrowsize=0.7];
 root [label="Protection against silent data corruption", fillcolor="#34495E", fontcolor=white];
 hw [label="Hardware-level\nprotection"]; rep [label="Replication-based\nprotection"]; ckpt [label="Checkpoint/restart\nwith verification"]; app [label="Application-level\nprotection"];
 root -> {hw rep ckpt app};
 ecc [label="Error-correcting\ncode (ECC) memory", fillcolor=white]; hard [label="Radiation-hardened\nand redundant circuits", fillcolor=white];
 dmr [label="Dual modular\nredundancy (DMR)", fillcolor=white]; tmr [label="Triple modular\nredundancy (TMR)", fillcolor=white];
 roll [label="Periodic checkpoint,\nverification, rollback", fillcolor=white];
 da [label="Data-analytic detectors\n(statistical prediction)", fillcolor=white]; abft [label="Algorithm-based fault\ntolerance (ABFT)", fillcolor="#D5E8D4", color="#2E7D32", penwidth=1.6];
 hw -> {ecc hard}; rep -> {dmr tmr}; ckpt -> roll; app -> {da abft};
}
G
dot -Tpng -Gdpi=220 f1.dot -o "$OUT/fig1.png"

# Fig 2 methodological framework
cat > f2.dot <<G
digraph G { rankdir=TB; ranksep=0.3; bgcolor=white;
 node [shape=box, style="filled", fontname="$FONT", fontsize=11, width=6.2, color="#34495E"];
 edge [color="#34495E", arrowsize=0.7];
 a [label="Research philosophy: Pragmatism\n(with a falsificationist stance toward empirical claims)", fillcolor="#34495E", fontcolor=white];
 b [label="Research approach: Deductive hypothesis testing informed by design reasoning", fillcolor="#5D6D7E", fontcolor=white];
 c [label="Research strategy: Design Science Research Methodology (DSRM)", fillcolor="#85929E", fontcolor=white];
 d [label="Research design: Quantitative controlled experiments + analytical modeling", fillcolor="#AEB6BF"];
 e [label="Data collection: Fault-injection campaigns and runtime measurements", fillcolor="#D6DBDF"];
 f [label="Data analysis: Wilson intervals, Wilcoxon signed-rank tests, Holm correction, model fitting", fillcolor="#EBEDEF"];
 a->b->c->d->e->f;
}
G
dot -Tpng -Gdpi=220 f2.dot -o "$OUT/fig2.png"

# Fig 3 DSRM
cat > f3.dot <<G
digraph G { rankdir=LR; nodesep=0.3; ranksep=0.35; bgcolor=white;
 node [shape=box, style="rounded,filled", fontname="$FONT", fontsize=10, fillcolor="#EEF2F7", color="#34495E", width=1.5, height=0.9];
 edge [color="#34495E", arrowsize=0.7];
 p1 [label="1. Identify\nproblem and\nmotivate"]; p2 [label="2. Define\nobjectives of\na solution"]; p3 [label="3. Design and\ndevelopment\n(ASTRA)"]; p4 [label="4. Demonstration\n(three workload\nclasses)"]; p5 [label="5. Evaluation\n(analysis +\nfault injection)"]; p6 [label="6. Communication\n(paper and\nartifacts)"];
 p1->p2->p3->p4->p5->p6;
 p5->p3 [label=" iterate", style=dashed, fontname="$FONT", fontsize=9, constraint=false];
 p6->p2 [label=" iterate", style=dashed, fontname="$FONT", fontsize=9, constraint=false];
}
G
dot -Tpng -Gdpi=220 f3.dot -o "$OUT/fig3.png"

# Fig 4 ASTRA architecture
cat > f4.dot <<G
digraph G { rankdir=TB; ranksep=0.35; bgcolor=white;
 node [shape=box, style="filled", fontname="$FONT", fontsize=11, width=5.8, color="#34495E"];
 edge [color="#34495E", arrowsize=0.7];
 app [label="Application kernel (e.g., matrix product, CG iteration, DNN layer)", fillcolor=white, style="dashed"];
 inv [label="Invariant layer\nSelects the algebraic, randomized, recurrence, or conservation invariant", fillcolor="#D6EAF8"];
 det [label="Detection layer\nEvaluates the invariant at low cost against a precision-aware threshold", fillcolor="#D5F5E3"];
 loc [label="Localization layer\nIdentifies location and magnitude of the error where possible", fillcolor="#FCF3CF"];
 rec [label="Recovery layer\nIn-place correction -> local recomputation -> self-healing -> rollback", fillcolor="#FADBD8"];
 app->inv->det->loc->rec;
 rec->app [label=" corrected state", fontname="$FONT", fontsize=9, style=dashed, constraint=false];
}
G
dot -Tpng -Gdpi=220 f4.dot -o "$OUT/fig4.png"

# Fig 5 taxonomy
cat > f5.dot <<G
digraph G { rankdir=TB; nodesep=0.2; ranksep=0.4; bgcolor=white;
 node [shape=box, style="rounded,filled", fontname="$FONT", fontsize=10, color="#34495E"];
 edge [color="#34495E", arrowsize=0.7];
 r [label="Exploitable algorithmic invariants", fillcolor="#34495E", fontcolor=white, fontsize=11];
 f1 [label="Family I\nAlgebraic checksum\ninvariants", fillcolor="#D6EAF8"];
 f2 [label="Family II\nRandomized verification\ncertificates", fillcolor="#D5F5E3"];
 f3 [label="Family III\nConvergence and\nrecurrence invariants", fillcolor="#FCF3CF"];
 f4 [label="Family IV\nDomain conservation\ninvariants", fillcolor="#FADBD8"];
 r->{f1 f2 f3 f4};
 e1 [label="Checksum-encoded\nmatrices\nDetect + locate + correct", fillcolor=white];
 e2 [label="Freivalds check,\nresidual checks\nDetect (probabilistic)", fillcolor=white];
 e3 [label="True vs. recursive residual,\nA-conjugacy\nDetect + self-heal", fillcolor=white];
 e4 [label="Mass/energy conservation,\nnormalization, bounds\nDetect (approximate)", fillcolor=white];
 f1->e1; f2->e2; f3->e3; f4->e4;
}
G
dot -Tpng -Gdpi=220 f5.dot -o "$OUT/fig5.png"

# Fig 7 recovery flowchart
cat > f7.dot <<G
digraph G { rankdir=TB; ranksep=0.3; nodesep=0.35; bgcolor=white;
 node [fontname="$FONT", fontsize=10, color="#34495E", style=filled, fillcolor="#EEF2F7"];
 edge [color="#34495E", arrowsize=0.7, fontname="$FONT", fontsize=9];
 s [label="Detector fires\n(discrepancy > threshold)", shape=box, style="rounded,filled", fillcolor="#34495E", fontcolor=white];
 q1 [label="Single error\nlocalized?", shape=diamond];
 a1 [label="In-place correction", shape=box, fillcolor="#D5F5E3"];
 q2 [label="Corrupted operation\nidentifiable?", shape=diamond];
 a2 [label="Local recomputation", shape=box, fillcolor="#D5F5E3"];
 q3 [label="Convergent\niterative method?", shape=diamond];
 a3 [label="Restart from last\nverified iterate", shape=box, fillcolor="#FCF3CF"];
 a4 [label="Roll back to last\nverified checkpoint", shape=box, fillcolor="#FADBD8"];
 v [label="Re-verify and resume", shape=box, style="rounded,filled", fillcolor=white];
 s->q1; q1->a1 [label=" yes"]; q1->q2 [label=" no"]; q2->a2 [label=" yes"]; q2->q3 [label=" no"]; q3->a3 [label=" yes"]; q3->a4 [label=" no"];
 {a1 a2 a3 a4}->v;
 {rank=same; q1 a1} {rank=same; q2 a2} {rank=same; q3 a3}
}
G
dot -Tpng -Gdpi=220 f7.dot -o "$OUT/fig7.png"

# Fig 10 experimental workflow
cat > f10.dot <<G
digraph G { rankdir=LR; nodesep=0.3; ranksep=0.3; bgcolor=white;
 node [shape=box, style="rounded,filled", fontname="$FONT", fontsize=10, fillcolor="#EEF2F7", color="#34495E", height=0.8];
 edge [color="#34495E", arrowsize=0.7];
 w [label="Workloads\n(dense LA, sparse\nCG, DNN training)"];
 g [label="Golden runs\n(fault-free\nreference + FP rate)"];
 i [label="Fault injection\n(binary level,\nframework level)"];
 p [label="Protected runs\n(ASTRA and\n4 baselines)"];
 m [label="Measurement\n(coverage, overhead,\np_c, waste, fidelity)"];
 s [label="Statistical\nanalysis and\nmodel comparison"];
 w->g->i->p->m->s;
}
G
dot -Tpng -Gdpi=220 f10.dot -o "$OUT/fig10.png"
