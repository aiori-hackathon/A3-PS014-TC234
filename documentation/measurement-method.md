# Measurement methodology notes

NetCompare adapts the RFC 2330 framework's emphasis on explicit metrics, measurement points, conditions, timestamps and reproducibility. Each result is an end-to-end observation at a participant endpoint. It includes the device, local Wi-Fi/Ethernet, access network, ISP path and destination.

- RTT: repeated ICMP echo probes; OS ping timing and ICMP treatment can affect results.
- Loss: missing replies divided by sent probes; only approximates application packet loss.
- DNS: one local resolver lookup, including cache effects.
- Throughput: capped HTTP download. Upload remains absent unless an operator supplies a controlled upload endpoint.
- Loaded jitter: currently an unloaded RTT variation proxy. The agent deliberately does not create competing traffic; a controlled loaded-jitter test needs a managed endpoint and concurrent cross traffic.
- Wi-Fi signal/local latency: optional fields. Platform adapters can be added; unknown values stay null.

Do not interpret medium averages as causal ISP comparisons. Keep participant consent, location granularity low, medium evidence separate from IP geolocation, and repeated observations grouped by participant in uncertainty analysis.
