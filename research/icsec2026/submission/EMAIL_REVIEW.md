Dear Mr. Borworntat Dendumrongkul:

Congratulations! Your paper #1571357468 ('Timed-Automata Verification of Payload-Link Supervision, Watchdog Gating, and A/B Boot Policy in STM32 Flight Software') for ICSEC 2026 has been Accepted for presentation at ICSEC 2026.

Please prepare and submit the Camera-Ready version of your paper by 5 November 2026.

We kindly ask you to carefully revise your manuscript according to the reviewers’ comments before submitting the final version.

Before submitting the Camera-Ready Paper, please ensure that your manuscript is in PDF format and has been verified using IEEE PDF eXpress. All submissions must be in PDF format. Please refer to the IEEE PDF eXpress instructions for the verification process.

The reviews are below or can be found at 1571357468.

Final Round Review 1

Strengths: Please describe the main strengths of this paper.

Weaknesses / Major Issues: Please describe the main weaknesses or major issues that should be addressed.

Minor Issues / Suggestions: Please provide any minor issues, corrections, or suggestions for improvement.

Comments to Authors: Please provide your overall comments and constructive feedback to the authors.

Final Round Review 2

Strengths: Please describe the main strengths of this paper.

A careful UPPAAL verification of three practical flight-software mechanisms, with constants traced to the source code and a real defect found and fixed.

Weaknesses / Major Issues: Please describe the main weaknesses or major issues that should be addressed.

The scheduling jitter J = 2 ms is assumed rather than measured, and all derived bounds depend on it. One recorded interval exceeds its bound by 17 ms and remains unexplained, which raises the question of whether the assumed jitter is large enough. Please measure the jitter on the target or explain the exceedance.

Minor Issues / Suggestions: Please provide any minor issues, corrections, or suggestions for improvement.

Comments to Authors: Please provide your overall comments and constructive feedback to the authors.

A careful and well-documented verification study. Please narrow the model–code gap for at least one mechanism, and justify the jitter assumption with measurements.

Final Round Review 3

Strengths: Please describe the main strengths of this paper.

The paper presents a clear formal verification method for embedded flight software. The results are well organized, and finding a real bootloader defect is a useful contribution. The hardware test data also supports the study.

Weaknesses / Major Issues: Please describe the main weaknesses or major issues that should be addressed.

The verification is based on simplified models and does not fully cover the actual firmware. The hardware validation is mainly focused on the payload link, while the watchdog and boot mechanisms need more experimental testing.

Minor Issues / Suggestions: Please provide any minor issues, corrections, or suggestions for improvement.

The authors should improve the explanation of some technical terms and make the figures easier to read. More details about the timing assumptions and the unresolved 17 ms difference would help readers understand the results.

Comments to Authors: Please provide your overall comments and constructive feedback to the authors.

This is a good technical paper with a clear methodology and useful results. The formal verification and defect identification are valuable. I suggest adding more hardware tests and explaining the limitations more clearly.

Regards,
The conference chairs
