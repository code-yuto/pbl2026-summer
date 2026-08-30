# Design of a Smart Irrigation Monitoring System Using Soil Moisture / Water Level Sensors and an LLM

**Hardware Team · Edge Team · Backend Team**
**Project:** pbl2026-summer

## Abstract

This project (pbl2026-summer) continuously monitors field conditions using soil moisture and water level sensors, and builds a smart irrigation monitoring system that combines immediate threshold-based checks on the edge microcontroller with contextual anomaly detection on the backend, where an LLM (large language model) reasons over the sensor data together with weather forecast information. The system is split into three layers — hardware, edge, and backend — and each team depends on only a single coupling point, "Send data (JSON)," which allows the three teams to develop completely independently in parallel. When a threshold is exceeded, the LLM step is bypassed and an alert is sent immediately; otherwise, normal sensor data is combined with the weather forecast and passed to the LLM, which detects contextual inconsistencies such as sensor faults or leaks and proposes whether irrigation is needed and how much. The final result is delivered to the user through an app, LINE, or Discord. In addition to this remote pathway, the edge device also drives an on-board RGB LED whose color is set by the same threshold logic, so that anyone standing near the device can read the current field status the moment it is powered on, with no network connection or app required.

**Keywords:** IoT, smart agriculture, edge computing, LLM, anomaly detection

## 1. Introduction

In recent years, the integration of the Internet of Things (IoT) into agriculture has attracted increasing attention as a promising approach to improving water-use efficiency, reducing manual intervention, and enabling data-driven irrigation management. IoT-based smart irrigation systems can continuously collect field-level information such as soil moisture, environmental conditions, and water availability, allowing irrigation decisions to respond to the actual state of the agricultural environment rather than relying solely on fixed schedules or manual observations [1], [2]. Recent studies have demonstrated that combining real-time soil-moisture sensing with weather information can further improve irrigation scheduling by accounting for forthcoming rainfall and changing environmental conditions [1], [3]. In addition, the integration of edge computing with IoT systems enables real-time processing of field data closer to the sensing devices, reducing dependence on cloud processing and supporting more responsive agricultural applications [4].

Despite these advances, conventional scheduled irrigation and visual inspection remain limited in their ability to respond rapidly to dynamic field conditions. Fixed irrigation schedules may result in unnecessary water consumption when sufficient rainfall is expected, while manual monitoring can delay the identification of abnormal conditions such as excessive or insufficient water levels, sensor abnormalities, or potential leakage. Recent IoT-based irrigation architectures have therefore emphasized continuous sensing, real-time data transmission, threshold-based decision making, and automated notification mechanisms to support timely intervention [1]. Moreover, research on agricultural sensor data has highlighted the importance of detecting abnormal patterns in real-time sensing streams, particularly when reliable monitoring is required for autonomous or semi-autonomous systems [5].

To address these limitations, this project designs and implements an IoT-based smart irrigation system capable of continuously monitoring soil moisture and water level in real time, detecting abnormal conditions, and immediately reporting potential anomalies. Beyond simple threshold-based control, the system incorporates external information, particularly weather forecasts, into the irrigation decision process. This approach follows recent research demonstrating that the integration of real-time field observations and weather forecasts can support more adaptive irrigation scheduling and improve water-management efficiency [2], [3].

From a system-engineering perspective, the development is divided into three teams: hardware, edge, and backend. The hardware layer is responsible for sensing and acquiring physical environmental data; the edge layer performs local data processing and decision-making; and the backend layer manages data storage, visualization, notification, and system-level services. This layered structure is consistent with recent IoT-based smart irrigation architectures that separate field devices, computational layers, and cloud or dashboard services to facilitate real-time monitoring and scalable system development [1], [4]. To enable parallel development, the interfaces between the three teams are intentionally minimized and clearly defined, allowing each team to develop and test its components independently while maintaining system interoperability.

This report presents the overall system architecture in Section 2, followed by the activity diagram and processing flow in Section 3. Section 4 discusses the rationale behind the inter-team interface design and explains how the proposed interfaces support modularity and parallel development. Finally, Section 5 summarizes the main contributions of the project and discusses potential directions for future development, including more advanced anomaly detection, predictive irrigation, and further integration of edge intelligence and external environmental data.

A further motivation for this design concerns usability. Many existing IoT-based irrigation and water-level monitoring systems expose only raw sensor readings and time-series charts, which require domain expertise to interpret correctly; a non-expert user such as a field operator or farmer may find it difficult to judge, from numbers alone, whether a given reading is actually a problem and what action, if any, is needed. To close this gap, the backend in this project deliberately separates the anomaly decision from its explanation: the risk level itself is always computed by deterministic, auditable threshold logic, while the LLM is used only afterward, to translate that decision and the surrounding sensor/weather context into a short, plain-language summary and recommendation. In this way, the LLM does not replace the decision-making logic but instead acts as a readability layer that makes the system's output directly actionable for non-expert users.

A complementary usability feature addresses a different gap: the remote notification pathway above assumes the user is checking a phone or a dashboard, but a person physically walking past the field device has no easy way to know its status without doing so. To solve this, the edge device also exposes its status directly and locally through an RGB LED wired to the microcontroller. Because the LED color is derived from the same threshold logic used to decide whether to alert, simply supplying power to the device is enough to read its current status on the spot — no app, login, or network connection is needed, and the indication remains available even if Wi-Fi or the backend is unreachable. Section 2.4 describes this feature and its color mapping in detail.

## 2. System Architecture

The system consists of three layers: hardware, edge, and backend. Figure 1 shows the overall system architecture.

*Figure 1: System architecture — three-layer structure and team responsibilities*

### 2.1 Hardware Team (Sensors & Circuit)

Analog values are read from soil moisture and water level sensors installed in the field. The hardware team is responsible for sensor selection, wiring, and power design, and passes the values to the microcontroller downstream as analog inputs. Figure 2 shows the circuit design, and Figure 3 shows the assembled hardware used in the experiment.

**➜ Insert here:** save the circuit design diagram as `docs/images/circuit-diagram.png`.

![Figure 2: Circuit diagram of the sensor and RGB LED wiring](images/circuit-diagram.png)

*Figure 2: Circuit diagram showing the wiring of the soil moisture sensor, water level sensor, and RGB LED to the microcontroller.*

**➜ Insert here:** save a photo of the actual assembled hardware as `docs/images/hardware-setup.jpg`.

![Figure 3: Photo of the assembled experimental hardware](images/hardware-setup.jpg)

*Figure 3: Photograph of the actual experimental setup, including the sensors, microcontroller, and RGB LED.*

### 2.2 Edge Team (Arduino Firmware)

Firmware on the microcontroller aggregates the sensor values and performs a threshold check. If a value exceeds the normal range (Anomaly), it takes the "immediate path," sending an alert right away without going through the LLM. If the values are within the normal range (Normal), the sensor data is packaged as JSON and sent to the backend over HTTP or MQTT.

### 2.3 Backend Team (LLM & API)

The backend fetches forecast data from a weather API in addition to the incoming JSON data, and passes both to the LLM. The LLM performs a "contextual check" to verify that the sensor values and weather information are consistent. If they conflict (Inconsistent), it flags a contextual anomaly that may indicate a leak or sensor fault. If they are consistent (Consistent), it generates a normal report including the irrigation need and amount. The final result is delivered to the user via an app, LINE, or Discord.

### 2.4 On-Device Status Indicator (RGB LED)

Alongside the JSON data it sends to the backend, the edge firmware drives a common-cathode RGB LED wired directly to the microcontroller. Its purpose is to make the field status readable on the spot: because the LED color is computed from exactly the same threshold logic that decides whether to alert, a person near the device only needs to look at it — once the device is powered, the current status is visible immediately, with no dependence on Wi-Fi, the backend, or a phone app. This makes the LED useful both as a quick check during routine visits to the field and as a fallback indicator if the network connection or backend is temporarily unavailable.

The color is derived from the same two readings — water level and soil moisture — but is deliberately limited to four colors rather than one color per combination, so that it can be read correctly at a glance even under bright outdoor sunlight, where closely related hues (e.g., cyan vs. light blue) are hard to tell apart. The four LED colors are also chosen to align with the four-level risk classification (`normal` / `medium` / `high` / `critical`) that the backend already computes and shows on the dashboard, so that the local, offline LED indication and the remote, dashboard-based indication speak the same "language":

| LED Color | Category | Corresponds to | Condition |
| --- | --- | --- | --- |
| Red | Hardware anomaly | (no dashboard equivalent — a device-level fault, not a risk level) | Sensor disconnected/short-circuited, or water level abnormally high (flood); reading is not trustworthy and bypasses the LLM to notify immediately |
| Green | No problem | `normal` | Water level full and soil moisture not dry |
| Yellow | Caution | `medium` | Water level in the medium band (reserve decreasing) while soil moisture is still acceptable |
| Orange | Needs attention | `high` / `critical` | Soil is dry, or the water reserve is low, on at least one of the two readings |

This design keeps a clear separation between two different kinds of signal: red is reserved for a fault in the device itself (the sensor cannot be trusted), while green/yellow/orange communicate the field's actual drought risk using the same three severity steps the backend already applies to sensor readings. Because only four colors are used, a field operator only needs to learn a short color code once, after which the field's status can be judged correctly from a distance, without reading any numeric sensor value. Internally, the underlying JSON `type` field sent to the backend still distinguishes all ten specific sensor conditions (see Section 4); only the physical LED color itself is simplified to four, so this change required no modification to the backend or dashboard.

## 3. Processing Flow (Activity Diagram)

Figure 4 is an activity diagram showing the processing order along each team's swim lane. The thick horizontal bars represent fork/join points, indicating that soil moisture and water level are read in parallel.

*Figure 4: Activity diagram — processing order and swim lanes*

Processing proceeds as follows. The hardware team first reads soil moisture and water level in parallel (fork), and the edge team aggregates them and performs the threshold check (the decision after the join). If the result is an anomaly (out of range, link loss, etc.), the LLM is bypassed and an alert is sent immediately. If normal, the data is sent to the backend as JSON and combined with weather data for an LLM consistency check. If the check result is inconsistent, a contextual anomaly is flagged; if consistent, a normal irrigation report is generated. In either case, the user is notified and processing ends.

Figures 5 and 6 show the actual output produced by this flow: the backend dashboard displaying real-time sensor data and risk classification, and an example Discord alert notification, respectively.

**➜ Insert here:** save a screenshot of the actual, running dashboard as `docs/images/dashboard-screenshot.png`.

![Figure 5: Screenshot of the backend dashboard](images/dashboard-screenshot.png)

*Figure 5: Screenshot of the dashboard showing real-time sensor data and risk classification.*

**➜ Insert here:** save a screenshot of the Discord notification as `docs/images/discord-notification.png`.

![Figure 6: Screenshot of a Discord alert notification](images/discord-notification.png)

*Figure 6: Screenshot of an alert notification delivered to Discord.*

## 4. Inter-Team Interface Design

A key design decision in this project is limiting the coupling point between the three teams to a single interface: "Send data (JSON)." As long as this JSON schema is agreed upon in advance, the hardware, edge, and backend teams can each develop independently in parallel, shortening the development timeline and reducing inter-team dependencies.

| Coupling Point | Description | Between Teams |
| --- | --- | --- |
| Send data (JSON) | Sensor data within threshold sent as JSON over HTTP/MQTT | Edge → Backend |
| Send alert immediately | Immediate alert bypassing the LLM when a threshold is exceeded | Edge → Notification |

By minimizing the coupling point in this way, the hardware team can change sensor specifications, the edge team can adjust threshold logic, and the backend team can improve LLM prompts or API integration, all without waiting on the other teams' implementations.

## 5. Conclusion and Future Work

This report presented the architecture and processing flow of a smart irrigation monitoring system that combines soil moisture and water level sensors with an LLM. By distinguishing between immediate threshold-based alerts and LLM-driven contextual anomaly detection, the system aims to respond quickly to urgent anomalies while also providing fine-grained irrigation recommendations that account for weather conditions. The system also addresses usability at both ends of the pipeline: remotely, the LLM turns raw sensor and weather data into a plain-language summary for non-expert users, while locally, the on-device RGB LED lets anyone near the field read the current status the moment the device is powered, without needing the network, the backend, or an app.

Future work includes the following:

- Calibrating threshold parameters using real hardware sensors, informed by agronomic expert knowledge (e.g., crop- and soil-specific guidelines) rather than sensor readings alone
- Moving beyond a general-purpose LLM prompt toward decision logic specialized for each deployment's crop type and land/soil characteristics (e.g., site-specific prompting, retrieval augmentation, or fine-tuning), further improving accuracy and reducing false positives
- Extending the system from status notification to closed-loop automatic irrigation, in which the backend's recommendation directly actuates a valve or pump rather than only alerting the user
- Optimizing the user experience for each notification channel (App / LINE / Discord)
- Validating sensor power supply and weatherproofing for long-term operation

## Acknowledgments

We thank everyone who contributed to this project for their support.

## References

1. pbl2026-summer project materials, "System Architecture."
2. pbl2026-summer project materials, "Activity Diagram."
3. M. A. et al., "IoT-based smart irrigation management system to enhance agricultural water security using embedded systems, telemetry data, and cloud computing," *Results in Engineering*, 2024, 102829. DOI: 10.1016/j.rineng.2024.102829
4. J. Jamal et al., "Real-Time Irrigation Scheduling Based on Weather Forecasts, Field Observations, and Human-Machine Interactions," *Water Resources Research*, 2023.
5. "AquaCrop Plug-in-PSO: A novel irrigation scheduling optimization framework for maize to maximize crop water productivity using in-season weather forecast and crop yield estimation," *Agricultural Water Management*, vol. 306, 2024, 109153. DOI: 10.1016/j.agwat.2024.109153
6. "A Comprehensive IoT edge based smart irrigation system for tomato cultivation," *Internet of Things*, vol. 28, 2024, 101356. DOI: 10.1016/j.iot.2024.101356
7. N.-T. Nguyen, R. Heldal, and P. Pelliccione, "Concept-drift-adaptive anomaly detector for marine sensor data streams," *Internet of Things*, vol. 28, 2024, 101414. DOI: 10.1016/j.iot.2024.101414

---

# 日本語訳

## 土壌水分・水位センサーとLLMを用いたスマートかんがい監視システムの設計

**ハードウェアチーム・エッジチーム・バックエンドチーム**
**プロジェクト:** pbl2026-summer

### 要旨

本プロジェクト(pbl2026-summer)は、土壌水分センサーと水位センサーを用いて圃場の状態を継続的に監視し、エッジ側のマイクロコントローラによる即時のしきい値判定と、バックエンド側でのコンテキストに基づく異常検知を組み合わせたスマートかんがい監視システムを構築する。バックエンドでは、LLM(大規模言語モデル)がセンサーデータと気象予報情報を突き合わせて推論を行う。システムはハードウェア・エッジ・バックエンドの3層に分割されており、各チームは「データ送信(JSON)」という単一の結合点のみに依存するため、3つのチームは完全に並行して独立に開発を進めることができる。しきい値を超えた場合はLLMのステップを経由せず即座にアラートが送信され、それ以外の通常のセンサーデータは気象予報と組み合わされてLLMに渡され、LLMはセンサー故障や漏水などのコンテキスト上の矛盾を検知し、かんがいの要否とその量を提案する。最終結果はアプリ、LINE、またはDiscordを通じてユーザーに届けられる。これに加えて、エッジデバイスは同じしきい値ロジックによって色が決まるオンボードのRGB LEDも備えており、デバイスの近くにいる人は、電源が入った瞬間にネットワーク接続やアプリなしで現在の圃場の状態を読み取ることができる。

**キーワード:** IoT、スマート農業、エッジコンピューティング、LLM、異常検知

### 1. はじめに

近年、農業分野へのIoT(モノのインターネット)の統合は、水利用効率の向上、人手による介入の削減、データ駆動型のかんがい管理を実現する有望なアプローチとして注目を集めている。IoTベースのスマートかんがいシステムは、土壌水分、環境条件、水の利用可能量といった圃場レベルの情報を継続的に収集できるため、固定スケジュールや人手による観察のみに頼るのではなく、実際の農業環境の状態に応じてかんがいの判断を行うことが可能になる[1], [2]。近年の研究では、リアルタイムの土壌水分センシングと気象情報を組み合わせることで、今後の降雨や変化する環境条件を考慮した、よりきめ細かなかんがいスケジューリングが可能になることが示されている[1], [3]。さらに、IoTシステムへのエッジコンピューティングの統合により、センシング機器に近い場所で圃場データをリアルタイム処理できるようになり、クラウド処理への依存を減らし、より応答性の高い農業アプリケーションを支えている[4]。

こうした進展にもかかわらず、従来の定期的なかんがいスケジュールや目視点検は、動的に変化する圃場条件に迅速に対応する能力に限界がある。固定のかんがいスケジュールは、十分な降雨が見込まれる場合でも不要な水消費を招く可能性があり、一方で人手による監視は、過剰または不足した水位、センサー異常、潜在的な漏水といった異常状態の発見を遅らせる可能性がある。そのため、近年のIoTベースのかんがいアーキテクチャでは、継続的なセンシング、リアルタイムのデータ伝送、しきい値に基づく意思決定、そして自動通知の仕組みが重視され、迅速な対応を支援している[1]。また、農業センサーデータに関する研究では、特に自律・半自律システムにおいて信頼性の高い監視が求められる場合、リアルタイムのセンシングストリームにおける異常パターンの検出の重要性が指摘されている[5]。

これらの限界に対処するため、本プロジェクトでは、土壌水分と水位をリアルタイムで継続的に監視し、異常状態を検知し、潜在的な異常を直ちに報告できるIoTベースのスマートかんがいシステムを設計・実装する。単純なしきい値による制御にとどまらず、本システムはかんがいの意思決定プロセスに外部情報、特に気象予報を組み込んでいる。このアプローチは、リアルタイムの圃場観測と気象予報を統合することで、より適応的なかんがいスケジューリングを支援し、水管理の効率を改善できることを示す近年の研究に基づいている[2], [3]。

システム工学的な観点から、開発はハードウェア・エッジ・バックエンドの3チームに分割されている。ハードウェア層は物理的な環境データのセンシングと取得を担当し、エッジ層はローカルでのデータ処理と意思決定を行い、バックエンド層はデータの保存、可視化、通知、システムレベルのサービスを管理する。この階層構造は、フィールドデバイス・計算層・クラウドまたはダッシュボードサービスを分離し、リアルタイム監視とスケーラブルなシステム開発を容易にする、近年のIoTベースのスマートかんがいアーキテクチャと一致している[1], [4]。並行開発を可能にするため、3チーム間のインターフェースは意図的に最小限かつ明確に定義されており、各チームはシステムの相互運用性を保ちながら、自チームのコンポーネントを独立して開発・テストできる。

本報告書では、第2章で全体のシステムアーキテクチャを示し、続く第3章でアクティビティ図と処理フローを示す。第4章では、チーム間インターフェース設計の背景にある考え方を議論し、提案するインターフェースがどのようにモジュール性と並行開発を支えるかを説明する。最後に第5章で、本プロジェクトの主要な貢献をまとめ、より高度な異常検知、予測的かんがい、エッジインテリジェンスと外部環境データとのさらなる統合といった、今後の発展の方向性について議論する。

さらに、本設計にはユーザビリティの観点からの動機もある。既存の多くのIoTベースのかんがい・水位監視システムは、生のセンサー値や時系列グラフをそのまま提示するだけであり、それを正しく解釈するには専門知識が必要になる。現場の作業者や農家のような非専門家のユーザーにとっては、数値だけを見て、それが実際に問題なのか、何らかの対応が必要なのかを判断することは難しい場合が多い。このギャップを埋めるため、本プロジェクトのバックエンドでは、異常の判定とその説明を意図的に分離している。リスクレベル自体は常に決定論的で検証可能なしきい値ロジックによって算出され、LLMはその判定が下された後に初めて使用され、その判定結果と周辺のセンサー・気象コンテキストを、短く平易な言葉による要約と提案に翻訳する役割を担う。このようにLLMは意思決定ロジックを置き換えるものではなく、システムの出力を非専門家のユーザーにとってそのまま行動可能な形にする「可読性の層」として機能する。

これを補うもう一つのユーザビリティ機能もある。上記の遠隔通知は、ユーザーがスマートフォンやダッシュボードを確認していることを前提としているが、圃場のそばを通りかかった人が、それを行わずにデバイスの状態を知る手段は別に必要である。この課題に対応するため、エッジデバイスはマイクロコントローラに接続したRGB LEDを通じて、状態をその場で直接表示する機能も備えている。LEDの色は、アラートを出すかどうかを判断するのと同じしきい値ロジックから決まるため、デバイスに電源を入れるだけでその場で現在の状態を読み取ることができる。アプリやログイン、ネットワーク接続は一切不要であり、Wi-Fiやバックエンドに接続できない状況でも表示は維持される。この機能とその色の対応関係は第2.4節で詳しく説明する。

### 2. システムアーキテクチャ

システムはハードウェア・エッジ・バックエンドの3層で構成される。図1に全体のシステムアーキテクチャを示す。

*図1: システムアーキテクチャ ― 3層構造と各チームの役割分担*

#### 2.1 ハードウェアチーム(センサーと回路)

圃場に設置された土壌水分センサーと水位センサーからアナログ値を読み取る。ハードウェアチームはセンサーの選定、配線、電源設計を担当し、下流のマイクロコントローラへアナログ入力として値を渡す。図2に回路の設計図を、図3に実験で使用した実機の写真を示す。

**➜ ここに挿入:** 作成した回路の設計図を `docs/images/circuit-diagram.png` として保存する。

![図2: センサーとRGB LEDの配線を示す回路図](images/circuit-diagram.png)

*図2: 土壌水分センサー、水位センサー、RGB LEDのマイクロコントローラへの配線を示す回路図。*

**➜ ここに挿入:** 実際に組み立てた実験機器の写真を `docs/images/hardware-setup.jpg` として保存する。

![図3: 組み立てた実験機器の写真](images/hardware-setup.jpg)

*図3: センサー、マイクロコントローラ、RGB LEDを含む実際の実験セットアップの写真。*

#### 2.2 エッジチーム(Arduinoファームウェア)

マイクロコントローラ上のファームウェアがセンサー値を集約し、しきい値判定を行う。値が正常範囲を超えている場合(異常)は「即時経路」をとり、LLMを経由せずに直ちにアラートを送信する。値が正常範囲内の場合(正常)は、センサーデータをJSONとしてパッケージ化し、HTTPまたはMQTT経由でバックエンドに送信する。

#### 2.3 バックエンドチーム(LLMとAPI)

バックエンドは、受信したJSONデータに加えて気象APIから予報データを取得し、両方をLLMに渡す。LLMは「コンテキストチェック」を行い、センサー値と気象情報の整合性を検証する。両者が矛盾する場合(Inconsistent)は、漏水やセンサー故障を示唆しうるコンテキスト異常としてフラグを立てる。整合している場合(Consistent)は、かんがいの要否とその量を含む通常のレポートを生成する。最終結果はアプリ、LINE、またはDiscordを通じてユーザーに届けられる。

#### 2.4 オンデバイス状態表示(RGB LED)

エッジのファームウェアは、バックエンドへ送信するJSONデータに加えて、マイクロコントローラに直接接続されたコモンカソード方式のRGB LEDを駆動する。その目的は、圃場の状態をその場で読み取れるようにすることである。LEDの色は、アラートを出すかどうかを判断するのと全く同じしきい値ロジックから計算されるため、デバイスの近くにいる人はLEDを見るだけでよい。デバイスに電源が入っていれば、Wi-Fi・バックエンド・スマートフォンアプリのいずれにも依存せず、現在の状態を即座に確認できる。これにより、LEDは日常的な見回りの際の簡易確認手段としてだけでなく、ネットワーク接続やバックエンドが一時的に利用できない場合の予備的な表示手段としても役立つ。

色は水位と土壌水分という同じ2つの測定値から決まるが、組み合わせごとに個別の色を割り当てるのではなく、意図的に4色までに絞っている。これは、屋外の強い日差しの下でも一目で正しく読み取れるようにするためであり、シアンと水色のように近い色相は現場では区別しづらい。また、この4色は、バックエンドがすでに算出しダッシュボードにも表示している4段階のリスク分類(`normal` / `medium` / `high` / `critical`)と対応させてあり、ローカルでオフラインのLED表示と、遠隔のダッシュボード表示とが同じ「言葉」で状態を語れるようにしている。

| LEDの色 | カテゴリ | 対応するリスク分類 | 条件 |
| --- | --- | --- | --- |
| 赤 | 機械の異常 | (ダッシュボード側に対応なし — リスク分類ではなくデバイス自体の故障) | センサーの断線・短絡、または水位が異常に高い(冠水)。値は信頼できず、LLMを経由せず直ちに通知 |
| 緑 | 問題なし | `normal` | 水位が満水で、かつ土壌水分も乾燥していない |
| 黄 | 警戒 | `medium` | 水位が中程度の区分にあり(残量が減少中)、土壌水分はまだ許容範囲内 |
| 橙 | 要注意 | `high` / `critical` | 土壌が乾燥している、または水の残量が少ない(いずれか一方でも該当) |

この設計では、性質の異なる2種類の情報を明確に分けている。赤はデバイス自体の故障(センサーを信頼できない状態)専用の色であり、緑・黄・橙は、バックエンドがセンサー値に対してすでに適用しているのと同じ3段階の深刻度を用いて、圃場の実際の乾燥リスクを伝える。色を4つに絞ったことで、現場の作業者は短い色の意味を一度覚えるだけで、数値を一切読まずに、離れた場所からでも圃場の状態を正しく判断できるようになる。なお、バックエンドへ送信されるJSONの`type`フィールドは、内部的には元の10種類の詳細なセンサー状態を区別したまま維持されている(第4節参照)。今回簡略化したのはLEDの物理的な色のみであるため、バックエンドやダッシュボード側の変更は一切不要である。

### 3. 処理フロー(アクティビティ図)

図4は、各チームのスイムレーンに沿った処理順序を示すアクティビティ図である。太い横棒はフォーク/ジョイン点を表し、土壌水分と水位が並行して読み取られることを示している。

*図4: アクティビティ図 ― 処理順序とスイムレーン*

処理は次のように進む。まずハードウェアチームが土壌水分と水位を並行して読み取り(フォーク)、エッジチームがそれらを集約してしきい値判定を行う(ジョイン後の判断)。結果が異常(範囲外、リンク断など)であれば、LLMを経由せず直ちにアラートが送信される。正常であれば、データはJSONとしてバックエンドに送信され、気象データと組み合わされてLLMによる整合性チェックにかけられる。チェックの結果が不整合であればコンテキスト異常としてフラグが立てられ、整合していれば通常のかんがいレポートが生成される。いずれの場合もユーザーに通知が行われ、処理が終了する。

図5・図6は、このフローによって実際に得られる出力の例である。図5はリアルタイムのセンサーデータとリスク分類を表示するバックエンドのダッシュボード、図6はDiscordに届いたアラート通知の例を示す。

**➜ ここに挿入:** 実際に稼働しているダッシュボードのスクリーンショットを `docs/images/dashboard-screenshot.png` として保存する。

![図5: バックエンドのダッシュボードのスクリーンショット](images/dashboard-screenshot.png)

*図5: リアルタイムのセンサーデータとリスク分類を表示するダッシュボードのスクリーンショット。*

**➜ ここに挿入:** Discordの通知画面のスクリーンショットを `docs/images/discord-notification.png` として保存する。

![図6: Discordアラート通知のスクリーンショット](images/discord-notification.png)

*図6: Discordに届いたアラート通知のスクリーンショット。*

### 4. チーム間インターフェース設計

本プロジェクトにおける重要な設計上の決定は、3チーム間の結合点を「データ送信(JSON)」という単一のインターフェースに限定していることである。このJSONスキーマが事前に合意されている限り、ハードウェア・エッジ・バックエンドの各チームはそれぞれ並行して独立に開発を進めることができ、開発期間の短縮とチーム間依存の低減につながる。

| 結合点 | 説明 | チーム間 |
| --- | --- | --- |
| データ送信(JSON) | しきい値内のセンサーデータをHTTP/MQTT経由でJSONとして送信 | エッジ → バックエンド |
| 即時アラート送信 | しきい値超過時にLLMを経由せず即座にアラートを送信 | エッジ → 通知 |

このように結合点を最小限にすることで、ハードウェアチームはセンサー仕様を変更でき、エッジチームはしきい値ロジックを調整でき、バックエンドチームはLLMプロンプトやAPI連携を改善でき、それぞれが他チームの実装を待つことなく作業を進められる。

### 5. まとめと今後の課題

本報告書では、土壌水分センサーと水位センサーにLLMを組み合わせたスマートかんがい監視システムのアーキテクチャと処理フローを示した。しきい値に基づく即時アラートと、LLMによるコンテキストに基づく異常検知とを区別することで、本システムは緊急性の高い異常への迅速な対応と、気象条件を考慮したきめ細かなかんがい提案の両立を目指している。本システムは、パイプラインの両端でユーザビリティにも配慮している。遠隔側では、LLMが生のセンサー値や気象データを非専門家にも分かる平易な要約に変換し、現地側では、オンデバイスのRGB LEDによって、圃場の近くにいる人が電源を入れるだけで、ネットワーク・バックエンド・アプリのいずれにも頼らず現在の状態を読み取ることができる。

今後の課題として、以下が挙げられる。

- 実機センサーによる校正に加え、専門家の農学的知見(作物・土壌の種類ごとのガイドラインなど)に基づいてしきい値パラメータを設定する
- 汎用的なLLMプロンプトにとどまらず、各設置地点の作物や土地・土壌特性に特化した判断ロジック(サイト固有のプロンプト設計、検索拡張生成、あるいはファインチューニングなど)を構築し、精度向上と誤検知の低減をさらに進める
- 状態の通知にとどまらず、バックエンドの提案がバルブやポンプを直接制御する自動かんがい(クローズドループ制御)へとシステムを拡張する
- 各通知チャネル(アプリ/LINE/Discord)におけるユーザー体験の最適化
- 長期運用に向けたセンサーの電源供給と防水性の検証

### 謝辞

本プロジェクトにご協力いただいたすべての方々に感謝する。

### 参考文献

参考文献は原文(英語)の書誌情報をそのまま参照のこと(上記 References 参照)。
