# Omer

I build AI systems that have to work on real hardware, not just in a notebook.

MS in Artificial Intelligence at SUNY Buffalo. Four publications, three
first-place hackathon finishes, and a standing inability to fix my sleep
schedule.

[LinkedIn](https://linkedin.com/in/syed-omer-shah) ·
[syedomer@buffalo.edu](mailto:syedomer@buffalo.edu) ·
[Hugging Face](https://huggingface.co/OmerShah)

<img src="stats.svg" alt="GitHub activity" width="840">

---

### Right now

Bayesian optimisation for SPECT detector geometry, running on HPC. Searching a
design space that used to be explored by hand, one configuration at a time.

The same method pointed at polymer discovery, because the problem underneath is
identical: expensive simulations, and nowhere near enough budget to try
everything.

And [being-human](https://github.com/Syedomershah99/being-human), which learns
how you actually write from your own prompt history and makes the model write
like that instead of like a press release.

### Selected work

**[being-human](https://github.com/Syedomershah99/being-human)**
Voice matching from your own prompt history. It derives a personal AI-slop list by
log-odds contrast between your words and the model's, then verifies drafts
against a calibrated authorship test. Stdlib Python, no dependencies.
`pip install being-human`

**[MolFM-Lite](https://github.com/Syedomershah99/molfm-lite)**
Multi-modal molecular property prediction. 0.956 AUC. First author,
[arXiv:2602.22405](https://arxiv.org/abs/2602.22405).

**[Multimodal AAC Chatbot](https://github.com/Syedomershah99/Multimodal-AAC-Chatbot)**
An agentic pipeline for accessible communication. 1.10s latency, and 100%
routing accuracy across intents.

**[safe-dispatch](https://github.com/Syedomershah99/safe-dispatch)**
Reinforcement learning for power grid dispatch under hard safety constraints.
It closes to a 3% cost gap with zero violations.

**[FabViz](https://github.com/Syedomershah99/FabViz)**
Semiconductor yield analysis with SPC charts. There is a
[live demo](https://fabviz.streamlit.app), though Streamlit sleeps when idle,
so give it a moment.

### Publications

**MolFM-Lite**: Multi-Modal Molecular Property Prediction.
[arXiv:2602.22405](https://arxiv.org/abs/2602.22405), 2026

**VMatter**: AI-Enabled IoT Patient Monitoring. Oral, ICMLDSSIA-2025, Springer Nature

**A Quantitative Framework for Optimizing SPECT Design**. Oral, SNMMI 2026

**Multiplexing-Induced Ghost Artifact in SPECT**. Poster, SNMMI 2026

### Tools

PyTorch and the usual scientific Python stack. LangGraph and CrewAI for agentic
work, LoRA and quantisation for making large models fit, vector databases for
retrieval. Slurm and HPC when the job is too big for one machine, AWS when it
isn't. C++ when Python is too slow, which is more often than I would like.

### Hackathons

First at Next InTech Ideathon (300 teams), HackZ (350 teams), and Hack-the-Verse
(550+ teams). Three in a row, which I am choosing to read as signal rather than
variance.

---

Happy to talk about AI, research, or basketball. The first two I can help with.

<sub>No badge wall, no visitor counter, no trophy case. That was deliberate. The
activity card above is generated from my own data and committed to this repo, so
it cannot 503 the way the hotlinked ones did.</sub>
