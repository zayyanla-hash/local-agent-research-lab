# WeightForge · Diagnosing tool-call failures in open weights

A local agent can choose the right tool and still send arguments an application cannot parse. I tested whether a small adaptation could repair that interface, then checked whether the improvement carried over to stateful work.

I fine-tuned existing Qwen3.5-4B weights, selected the step-12 LoRA checkpoint, merged it into the BF16 parent and quantized the merged model to affine INT4. Against its matched INT4 parent, the resulting artifact passed **793 of 1,000** BFCL V4 static Python cases, up from **699**. Simple calls went from 343 to 362 of 400. Of the three 200-case categories, multiple-function selection went from 185 to 187, parallel calls from 84 to 124, and parallel calls with multiple possible functions from 87 to 120. Those four complete categories cover part of BFCL V4.

The improvement narrowed at the application boundary. On independently scored workflows, the deployment completed 14/16 versus 15/16 and introduced a recovery failure. In two lab-authored τ-bench retail tasks, the parent earned both native rewards and WeightForge earned one. The application blocked the candidate's attempt to change a fictional shipping address before consent. Under the corrected scripted-user stopping rule, both arms completed one task strictly. The original holdout stayed closed.

Separate mechanistic work edited 16 actual BF16 normalization parameters in another 4B checkpoint. On one fitted prefix, the desired-token margin rose 0.250 logits while the matched random edit moved it 0.000. The output still contained the duplicate ID. Restoring the parameters reproduced the original tensor, logits and generation. A CPU replay lets readers verify both edited tensor hashes themselves. The net gain of 94 BFCL cases came from the matched step-12 adaptation experiment.

At 2,048 prompt tokens and batch one, the selected deployment decoded 97.3 tokens/s versus 97.4 for its matched parent in the official fixed-length MLX benchmark. Median resident time to first token in a separate streaming probe was 977 ms versus 969 ms. The close decode times let us attribute the headline change to observed answer quality without claiming an inference speedup.

[Evidence and receipts](../evidence/) · [Reproduce the weight edit](../examples/README.md) · [Model lineage and runtime](../provenance/README.md) · [Technical manuscripts](../manuscripts/)

© 2026 Zayyan Latif. All rights reserved.
