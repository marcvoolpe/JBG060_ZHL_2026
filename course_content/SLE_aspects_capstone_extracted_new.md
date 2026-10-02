# SLE Aspects Extracted from the Capstone Lectures

This document consolidates the Social-Legal-Ethical (SLE) material contained in the three provided Capstone Data Challenge lectures. It stays within the content of the slides and distinguishes lecturer framing, examples, questions, and suggested literature. Page references refer to the uploaded lecture files.

## Source key

- **Lecture 1**: *Data and/in the social-legal-ethical (SLE) space*, Tjaša Petročnik.
- **Lecture 2**: *SLE lecture 2*, Gijs van Maanen.
- **Lecture 3**: *SLE lecture 3*, Gijs van Maanen.

---

## 1. What the SLE component is asking you to do

### Assignment and course expectations

From **Lecture 1, p. 3**:

- The SLE assignment is a **group essay of 2500 words**.
- It counts for **40% of the grade**.
- The stated deadline is **25 October**.
- The essay should focus on **one SLE aspect**.
- The work is expected to be **iterative**, providing a **justified reflection on the technical work and its implications across the CRISP-DM workflow under uncertainty**.
- The course contains **three lectures and four feedback sessions**.
- Because this is an advanced course, **engagement with relevant and prescribed literature is expected**.

From **Lecture 3, p. 13**:

- The SLE work requires actual research and should connect **data understanding** with **business understanding**.
- Students are told to reread relevant DSE / Advanced Data Science material and the detailed essay assignment on Canvas.
- The slide explicitly advises:
  - Formulate a **good problem and research question**.
  - Use **references with page numbers**.
  - Use stakeholder sources and academic search as starting points, then **snowball** through references.

### Core framing: technical choices are SLE choices

**Lecture 1, p. 5** frames the SLE space through the question of whether technology is ever neutral:

- A technical contribution must be considered together with the **ask** and its **real-world implications**.
- Technology exists in a context that determines:
  - what is technically feasible,
  - what is legally compliant,
  - what is ethically defendable,
  - what is socially acceptable.
- The central statement is: **technical choices = SLE choices**.

This means the SLE analysis is not meant to be detached from the technical project. It should interrogate how choices made in problem formulation, data selection, modelling, evaluation, and deployment affect people and institutions.

---

## 2. Data as a socially constructed phenomenon

### Data does not simply “show reality”

From **Lecture 1, p. 7**:

- Data is presented as a **socially constructed phenomenon** [Haggart and Tusikov 2023].
- The role of data can move from merely **“seeing”** the world to **prescribing and governing through data**.
- This raises questions such as:
  - What are we measuring?
  - What are we making actionable?
  - Whose way of “seeing” counts?
  - Who benefits from the resulting representation and action? [Jasanoff 2017]

### Predicting the future from past data

Also from **Lecture 1, p. 7**:

- Predictive systems often use historical data to infer future events.
- The slides cite Innerarity (2023): predictive analytics can give **prescriptive force to the status quo**.
- A stated risk is the **reproduction of structural inequities**.

### Data extraction, surveillance, and power

From **Lecture 1, p. 8**:

- When data is treated as a resource to exploit, there is a strong incentive to gather as much of it as possible.
- This can lead to **surveillance**, **asymmetries**, and **dependence** [Haggart and Tusikov 2023].

### SLE questions for a data project

Questions directly supported by the lecture framing include:

- What phenomena are represented in the data, and what is left out?
- Which groups are visible or invisible?
- Who defined the categories and measurements?
- What assumptions turn raw information into an “actionable” variable?
- Could historical patterns reproduce existing inequalities when used predictively?
- Does data collection create surveillance or dependency?
- Who controls the data and who has the power to act on it?

---

## 3. Digital humanitarianism: benefits, risks, and humanitarian principles

### Humanitarian crises are partly shaped by human decisions

From **Lecture 1, p. 9**:

- The impact of disasters reflects **human-made choices as well as natural causes**.
- The emergence of humanitarianism is connected in the slides to **colonial logics**. Madianou (2025) is cited for the argument that colonialism was both a cause of humanitarian suffering and a mechanism through which suffering became visible to Western publics.
- The lecture also introduces **disaster capitalism** [Klein in Madianou 2025], where emergencies can open previously inaccessible domains to capitalist incorporation.

### Potential benefits of the digital turn

The slides also recognize positive claims associated with digital humanitarianism:

- Digital humanitarianism can support a shift from **reactive** to **anticipatory** efforts.
- Data analytics may help:
  - understand aid needs,
  - map disaster impact,
  - optimize aid allocation,
  - reduce inefficiencies,
  - amplify community voices,
  - increase transparency.

These benefits are presented as claims in the literature cited by the lecture, rather than as guarantees.

### Humanitarian principles as a design criterion

From **Lecture 1, p. 10**:

- Information and ICT use do not become humanitarian simply because humanitarian organizations use them.
- To qualify as humanitarian, the design and execution should uphold the principles of:
  - **humanity**,
  - **impartiality**,
  - **neutrality**,
  - **independence**.

### Risks of unrepresentative or decontextualized data

Also from **Lecture 1, p. 10**:

- Unrepresentative or decontextualized data can create **blind spots** and embed assumptions.
- Those blind spots can undermine humanitarian principles and remove important contextual nuance.
- Digital innovations such as fraud-prevention systems or satellite tracking can create risks to the **dignity** and **fundamental rights** of crisis-affected people.
- Digital innovation may also further **commercial values**.

### Participation and accountability can become technocratic

The slides warn that:

- “Accountability” and “participation” can be reduced to **technocratic, measurable goals** or rhetoric.
- This may replace meaningful inclusion of affected populations in deliberative processes.
- Data analytics can become an **evidence base used to justify further aid projects to donors**.

This theme is developed further in Madianou’s “logic of audit”.

---

## 4. Madianou’s logics for analysing digital humanitarianism

**Lecture 2, p. 3** lists the following logics from Madianou:

1. Humanitarian accountability
2. Audit
3. Capitalism
4. Technological solutionism
5. Securitization
6. Resistance

The slides also emphasize that the **logics are interrelated**. The logic of resistance is listed, but the supplied lectures do not develop it in detail. Lecture 3 explicitly says “Skip resistance”.

---

## 5. Logic of humanitarian accountability

The detailed lecture treatment from the first session is limited, but the supplied slides support the following points:

- Humanitarian projects are expected to demonstrate accountability.
- Digital systems and metrics can be used to show evidence of effectiveness.
- A concern introduced in **Lecture 1, p. 10** is that accountability can become a set of **measurable technocratic goals** rather than meaningful participation.
- Data analytics can be used to justify projects to donors.

This theme leads directly into the logic of audit in Lecture 2.

---

## 6. Logic of audit

From **Lecture 2, p. 4**:

### What it is

- Donors demand **accountability**.
- Accountability creates demand for **metrics and data about the effectiveness of relief**.
- Aid organizations operate under **funding pressure** and shorter time spans.
- Madianou is quoted as arguing that people affected by crises, **through their data**, can become the basis by which aid projects are justified and legitimated.

### SLE implications

The lecture asks:

- How are **ZHL / ZOA funded**?
- How are projects made accountable to funders?
- What does this accountability structure mean for **data gathering**?

The broader SLE issue is that the need to satisfy audit requirements can shape what is measured, which outcomes count, and whose data becomes valuable.

### Suggested further reading

The slide points to:

- Michael Power
- Caitlin Rosenthal

---

## 7. Logic of capitalism

From **Lecture 2, p. 5**:

### Conventional framing

- The slide refers to Mandeville’s *Fable of the Bees* and the idea of **trickle-down**.
- A conventional view treats markets as separated or independent from other social domains, which can obscure questions of power.

### Wood: relations of production

The slide summarizes a historical account associated with Wood:

- From the 16th to 18th centuries, changes occurred in **relations of production**.
- Workers became **propertyless and dependent on work**.
- Owners became **dependent on workers**.
- Important elements include:
  - mutual dependencies,
  - production oriented toward profit,
  - law establishing different forms of property,
  - erasure or enclosure of collective property.
- These dynamics are linked to the emergence of **capitalism**.

### Pistor: capitalism and law

The lecture presents Pistor’s account as:

- Capitalism as a **legal regime** that can enable appropriation of collective resources for personal gain.
- Markets and capitalism are dependent on the **state**.

### Relevance to humanitarian work

The lecture raises:

- **Philanthrocapitalism**.
- Expansion of market influence.
- Links between capitalism and accountability.
- Questions of ownership in South Sudan:
  - Who owns what?
  - How does ownership influence relief support?
  - How does ownership affect what can and cannot be measured?

---

## 8. Sen: famines, food, and entitlement relations

Lecture 2 uses Amartya Sen’s entitlement approach as a major SLE framework.

### Against “instant economics”

From **Lecture 2, p. 8**:

- Sen rejects a simple direct causal relationship between **food availability** and **famine**.
- A situation with no aggregate food shortage can still contain severe deprivation.
- The missing issue is the **acquirement problem**: whether particular people can actually acquire food.

### Entitlement approach

The lecture quotes Sen’s definition of a person’s entitlement as the set of alternative commodity bundles the person can acquire through the legal channels available to someone in that position.

Two key concepts are highlighted:

- **Endowments**
- **Exchange entitlement mappings**

The slides ask students to compare, for example, a **peasant** and a **wage labourer** to see how different positions produce different possibilities for acquiring goods.

### Famine as failed entitlement relations

The stated takeaway is:

- Famines can be understood as **failed entitlement relations**.
- In modern societies, entitlement is closely connected to **ownership and exchange**.

### Degrees, temporality, and different forms of famine

From **Lecture 2, p. 9**:

- Sen’s relevance includes attention to the **degrees and temporality** of famine and hunger.
- The slide distinguishes **slump** and **boom famines**.
- Different famine dynamics can imply different responses and different consequences for actors’ **freedom**.

### Policy relevance and multidimensional problems

From **Lecture 2, p. 10**:

- Anticipation must recognize that the problem is **multidimensional**.
- The slide explicitly warns: **do not use one factor to predict famines**.
- The lecture asks how this warning relates to **flood prediction**, including the basic definitional question: “what is a flood?”
- A **well-functioning public sphere** is presented as important.

The slide also frames policy choices through questions such as:

- Cash or food?
- How can people acquire food?
- What response is appropriate?
- Should food be imported?
- What is the short-term versus long-term approach?
- What does “food production” mean in the relevant context?

### Project-level takeaways from Sen

From **Lecture 2, p. 11**:

- Take **business understanding** seriously in CRISP-DM.
- Specify:
  - which communities,
  - who within those communities,
  - where they are,
  - which entitlements matter.
- Analyse the interaction between:
  - flood prediction and relief measures,
  - relief measures and markets / society,
  - relief measures and the choice / autonomy of affected groups.
- Avoid becoming an **“instant data scientist”**.
- Do not assume easy cause-effect relationships.
- Explicitly acknowledge limitations, especially when interacting with stakeholders.
- Read reports, papers, and research, and prepare well for stakeholder meetings.

---

## 9. Technosolutionism

From **Lecture 3, p. 6**:

### Definition

Technosolutionism is presented, following Madianou, as the **desire to find technological solutions for complex social problems**.

### Core SLE concern

The problem is not simply that technology is used. The concern is that a technical system can redefine the problem around what the system can easily measure, classify, or solve.

### Example: GiveDirectly flood-response experiment in Nigeria

From **Lecture 3, p. 7**:

- A *New Humanitarian* investigation is used as an example.
- The slide states that project “success” can be defined on the basis of the well-being of those who are already easier to reach or better off.
- A local community leader is quoted saying that mismatches in names, phone numbers, and bank verification numbers resulted in applicants being **cut out of the process entirely**.

The SLE issue is exclusion produced by the technical and administrative requirements of the aid system.

---

## 10. Securitization

From **Lecture 3, p. 6**:

### Definition

Securitization is described as the use of technologies, including biometrics, to make populations **“legible”** through:

- classification,
- tracking,
- surveillance.

### Identity Management Systems example

From **Lecture 3, p. 8**, the slides list identity-management technologies used in migration / asylum contexts:

- **DIAS**: dialect identification assistance.
- **AmD**: reading mobile data carriers.
- **TraLiTa / HKL**: name transliteration and country-of-origin prediction.
- **LiBiAs**: facial-recognition system.

The slide includes a statement from BAMF vice-president Markus Richter describing a system designed to infer a person’s country of origin even when they have no documents.

### Dialect identification as a classification problem

From **Lecture 3, p. 9**:

- Automated speech processing reworks the older **LADO** logic.
- The system treats **language as a proxy for origin** despite sociolinguistic complexity.
- The training corpora described on the slide mainly include:
  - Arabic speakers in the US and Australia from the 1990s,
  - newscasters from the 2000s.

The slide depicts a process from **phonetics + prosodics**, through similarity to training corpora, to a dialect percentage and then an inferred country of origin.

### Compression of social complexity

**Lecture 3, p. 10** visually emphasizes the reduction of a large and linguistically diverse region, described as **19 countries and 472 million inhabitants**, into **five dialect categories plus “Other”**.

The SLE issue is the relationship between classification systems and the complexity they compress or erase.

---

## 11. How technology can change the problem itself

From **Lecture 3, p. 11**:

- Technologies can **change problems**.
- Sometimes this is beneficial, sometimes harmful.
- The lecture contrasts:
  - “How do we easily locate those in need and help them?”
  - with a reframed problem closer to “How can this technology help the people who are easiest to help, while demonstrating the technology’s commercial value?”

The slide asks a central project question:

> How do your technical choices relate to your more-than-technical problem?

The lecture also reminds students to review material on the **normative character of technological design** and points to classification literature such as Bowker and Star, *Sorting Things Out: Classification and Its Consequences*.

---

## 12. Anticipatory Action (AA) as an SLE-relevant field

Lecture 3 uses anticipatory action as a concrete domain in which the previous SLE concerns become visible.

### Definition

From **Lecture 3, p. 14**:

- Anticipatory action means acting **ahead of a predicted hazardous event** to prevent or reduce impacts on lives, livelihoods, and humanitarian needs before they fully unfold.
- It works best when:
  - activities are pre-agreed,
  - trigger thresholds or decision rules are pre-agreed,
  - decisions allow rapid release of **pre-arranged funding**.

The slide suggests case studies such as **Kenya and cash relief**, including the pros and cons of cash and the technical methods used.

### South Sudan example

From **Lecture 3, p. 15**:

- Eason-Calabria’s *Acting in Advance of Flooding: Early action in South Sudan* is highlighted as highly relevant.
- Examples of actions include:
  - **dyke building**,
  - **cash grants to female IDPs to buy wood**.
- The lecture tells students to note:
  - the focus on **camps**,
  - comments on **governance**.

### Timing, action selection, and targeting

From **Lecture 3, p. 16**, Chavez-Gonzalez et al. (2022) is used to emphasize:

- Unknowns, risks, and assumptions should be documented transparently.
- Built-in trade-offs should be acknowledged.
- Error risk should be mitigated.
- Three key design questions are:
  1. **Timing**
  2. **Activity selection**
  3. **Targeting**

The lecture also points to the **finance of anticipatory action**.

### Entitlements and livelihood systems

Also from **Lecture 3, p. 16**:

- Parodi (2024) is linked back to Sen’s idea of **entitlements**.
- The slide quotes the importance of agro-pastoral livelihoods in the Sahel, including reliance on rain-fed farming, livestock, pasture, and water.

The SLE implication is that a relief intervention cannot be evaluated only as a transfer of resources. It must be understood in relation to livelihood systems and people’s existing means of access to resources.

---

## 13. Information problems in anticipatory action

From **Lecture 3, p. 17**, Letz & Maxwell are used to identify several constraints:

- **Information overload**.
- Information not being available in the **right place**.
- Difficulty predicting **conflict**.
- The **politicized nature of data**.
- Lack of transparency around politically sensitive issues such as conflict-caused famine.
- Data is **not self-explanatory**, including when AI is used.

These points reinforce the earlier SLE message that adding more data or more sophisticated modelling does not remove questions of interpretation, institutions, politics, and power.

---

## 14. Anticipatory action as a science-policy hybrid

From **Lecture 3, p. 18**:

- Anticipatory action is often presented as something new, and the slide asks what follows from that framing.
- AA is described as a **science-policy hybrid**.
- There is more at stake than simply delivering “good relief”.
- A standing critical question is:
  - **Who writes what, and for what reason?**

This is a source-evaluation and power question: knowledge about crises is produced by particular actors, institutions, funders, and methods.

---

## 15. People-centred relief and distributional effects

From **Lecture 3, p. 19**, Breugen et al. are used to introduce a people-centred perspective on humanitarian logistics.

### Distribution is not only about equal quantities

The lecture highlights:

- **distributional preferences**,
- **envy**,
- **guilt**,
- the possibility that the **same distribution of resources can produce different levels of well-being**.

The quoted example argues that aid perceived as highly inequitable can contribute to:

- conflict,
- blockages,
- looting,
- assaults.

The slide also notes solidarity responses such as households sharing or redistributing aid, or people volunteering to help households that are worse off.

### SLE implication

An evaluation metric based only on how much aid is distributed can miss:

- perceived fairness,
- social relationships,
- community responses,
- differences in well-being.

---

## 16. Cash relief and market context

From **Lecture 3, p. 20**:

- Weiffen et al., *Cash and Cohesion in Crisis: On the Impacts of Anticipatory Cash Transfers in IDP Camps in South Sudan during Floods*, is highlighted for students interested in cash.
- The lecture links the paper to:
  - **groups**,
  - **entitlements**,
  - **location**,
  - the type of **market** that is present.

The slides tell students to follow references through **snowballing**.

### SLE implication

Cash is not a context-free intervention. Its effects depend on who receives it, where recipients are located, what markets exist, and what recipients can actually acquire.

---

## 17. Pastoral systems, indigenous knowledge, and intervention design

From **Lecture 3, p. 21**:

- Hassan, Stites, and Howe (2024), *Pastoralists’ Perspectives on Early Warning, Anticipatory Action, and Emergency Response*, is presented as useful.
- The lecture emphasizes the difference between formal anticipatory action and **indigenous knowledge**.
- Examples of indigenous indicators include:
  - weather observation,
  - animal behaviour.
- The study focuses on **pastoralists**, rather than IDPs in camps.

### SLE implication

The relevant knowledge system, livelihood system, and social setting differ across populations. A method developed for camp-based populations should not automatically be assumed to transfer to pastoralist communities.

---

## 18. Evaluating literature and evidence quality

The lectures treat source evaluation as part of SLE responsibility.

### Example of a potentially relevant but weak source

From **Lecture 3, p. 22**, a stakeholder-recommended source is evaluated critically:

- It may be interesting and relevant.
- The author’s background is noted: former refugee, PhD in mathematics.
- The method is described as **very brief / underdeveloped**.
- The writing and analysis are criticized for:
  - odd structure,
  - lack of references.
- The lecture suggests it may be useful as **first-person experience**, but perhaps not as social science.
- The key instruction is to **verify repeatedly**.
- The slide states: **“one source = no source”**.

### General source-evaluation questions

From **Lecture 3, p. 23**:

For SLE feedback, evaluate:

- What are you reading?
  - White paper?
  - Report?
  - Peer-reviewed paper?
  - Pre-publication?
  - Random webpage?
- Who wrote it?
- Who funded it?
- Does it use good methods?
- Does it back up its claims?
- Are its key sources convincing?
- What is the **foundation of the claims**?

The lecture mentions Daniel Maxwell and the Feinstein research center as an example of tracing an author’s institutional and field connections.

### Responsibility to verify with stakeholders

From **Lecture 3, p. 24**:

- Students are reminded that it is their responsibility to evaluate source quality.
- Preliminary results should be checked with **stakeholders and instructors**.

---

## 19. Cross-cutting SLE themes for the project

The following themes recur across the three lectures.

### 19.1 Problem definition

- Who defined the problem?
- Is the problem being reformulated around what a technology can easily measure or solve?
- Does the technical representation preserve the multidimensional nature of the real-world problem?
- What is excluded when the problem becomes a prediction or classification task?

### 19.2 Representation and classification

- Which people and conditions appear in the data?
- Which people are missing?
- Which categories are imposed?
- Are proxies, such as language for origin, defensible in the relevant social context?
- How much social complexity is compressed into simplified classes?

### 19.3 Power and accountability

- Who demands evidence and metrics?
- How do funding structures affect what is measured?
- Who controls data and technical infrastructure?
- Are metrics oriented toward affected populations, donors, technology providers, or other actors?

### 19.4 Inclusion and exclusion

- Do identity or administrative requirements exclude people with missing or inconsistent records?
- Who is easiest to reach and therefore most likely to be counted as a “successful” case?
- Does the system systematically disadvantage people with limited phone, banking, documentation, or other infrastructure access?

### 19.5 Equity and distribution

- Does equal resource distribution lead to equal well-being?
- How is fairness perceived by affected groups?
- Could intervention design produce envy, conflict, or social fragmentation?
- Could communities redistribute aid in ways the model does not anticipate?

### 19.6 Autonomy and entitlements

- What can affected people actually acquire with the resources provided?
- How do ownership, markets, work, mobility, and legal channels shape entitlements?
- How do relief measures affect choice and autonomy?

### 19.7 Surveillance, legibility, and securitization

- Does the intervention make people more trackable or surveyable?
- Is data collected because it is necessary for relief, or because technical systems make collection possible?
- Could humanitarian data be repurposed for identity management, security, or control?

### 19.8 Commercialization

- Are commercial values influencing problem definition or system design?
- Does success partly depend on demonstrating the commercial value of a technology?
- Are humanitarian organizations becoming dependent on private technological infrastructures?

### 19.9 Uncertainty and prediction

- Which unknowns, assumptions, and risks are embedded in the model?
- Are they documented transparently?
- Does the model rely too heavily on one predictive factor?
- Are difficult-to-predict phenomena such as conflict treated appropriately?
- Is the data interpreted as if it were self-explanatory?

### 19.10 Participation and knowledge

- Are affected populations meaningfully involved in decisions?
- Is participation reduced to a measurable indicator?
- Which knowledge systems count: institutional data, local experience, indigenous knowledge, or others?
- Who produces the evidence and for what purpose?

---

## 20. Derived SLE checklist across CRISP-DM

This section is a synthesis derived from the lecture content. The exact phase-by-phase checklist is not presented verbatim in the slides, but it follows the repeated instruction to reflect on SLE implications across the CRISP-DM workflow.

### Business understanding

- Who exactly is affected: which communities, groups, locations, and livelihood systems?
- What is the real-world problem, and who defines it?
- Which entitlements, ownership relations, markets, institutions, and governance arrangements shape the problem?
- Who funds the intervention and what accountability pressures follow?
- What would “success” mean to affected people, funders, implementers, and technology providers?

### Data understanding

- What does the dataset measure, and what does it fail to capture?
- Who is missing or underrepresented?
- How was the data produced, and by whom?
- Are there politically sensitive, commercial, or surveillance-related incentives behind collection?
- Are important contextual variables absent?

### Data preparation

- What exclusions are created by matching, cleaning, deduplication, ID verification, transliteration, or missing-data rules?
- Do categories simplify heterogeneous groups too aggressively?
- Are technical preprocessing choices producing socially meaningful classifications?

### Modelling

- Does the model rely on problematic proxies?
- Does it reproduce the status quo encoded in historical data?
- Are multidimensional problems reduced to one predictor?
- How are uncertainty, trade-offs, and difficult-to-predict dynamics represented?

### Evaluation

- Which metrics define model or project success?
- Do evaluation metrics reflect well-being, fairness, autonomy, and humanitarian principles?
- Who bears the costs of false positives, false negatives, missed cases, or misclassification?
- Are results checked against stakeholder knowledge and alternative evidence?

### Deployment

- Does deployment create new surveillance, dependency, or securitization risks?
- Could the technology change the problem around the people easiest to serve?
- Does deployment alter market relationships, entitlements, governance, or autonomy?
- Who controls the deployed system and the resulting data?
- Can affected people contest classifications or decisions?

---

## 21. Questions the lectures explicitly encourage you to ask

A compact set of lecturer-framed questions:

- How are your stakeholders funded?
- How are projects made accountable to funders?
- What does accountability mean for data gathering?
- Who owns what, and how does ownership influence relief support?
- Which communities? Who? Where? Which entitlements?
- How does flood prediction interact with relief measures?
- How do relief measures interact with markets and society?
- How do relief measures affect the choice and autonomy of affected groups?
- How do technical choices relate to the more-than-technical problem?
- What are the unknowns, risks, assumptions, and trade-offs?
- What is the right timing, action, and target group for anticipatory action?
- What information is missing, overloaded, politicized, or unavailable where it is needed?
- Who writes what, and for what reason?
- What kind of source are you reading, who wrote it, who funded it, and what supports its claims?

---

## 22. Literature and resources named in the slides

The following items are included because the lectures identify them as relevant or potentially useful. Their quality should still be independently evaluated, as Lecture 3 repeatedly stresses.

### General SLE / data / digital humanitarianism

- Haggart, Blayne and Natasha Tusikov. *The New Knowledge: Information, Data and the Remaking of Global Power*. Bloomsbury Publishing, 2023.
- Innerarity, Daniel. “Predicting the past: a philosophical critique of predictive analytics.” *IDP. Revista de Internet, Derecho y Política* 39 (2023).
- Jasanoff, Sheila. “Virtual, visible, and actionable: Data assemblages and the sightlines of justice.” *Big Data & Society* 4 (2017). DOI: 10.1177/205395171772447.
- Haas, Maria. “How AI learns, and what it misses: why data selection matters in humanitarian action.” *Humanitarian Law & Policy*, 14 August 2025. https://blogs.icrc.org/law-and-policy/2025/08/14/how-ai-learns-and-what-it-misses-why-data-selection-matters-in-humanitarian-action/
- Iazzolino, Gianluca and Nimesh Dhungana. “Prediction and data curation in digital humanitarianism.” *Big Data & Society* 12(3), 2025. DOI: 10.1177/20539517251361111.
- Kundu, Shreenik et al. “Need for ethical use of artificial intelligence in humanitarian data collection to address aid shortfalls.” *The Lancet Digital Health* (2026). DOI as given in slide: 10.1016/j.landig.2026.101045.
- Latonero, Mark. “Stop Surveillance Humanitarianism.” *The New York Times*, 11 July 2019.
- Madianou, Mirca. *Technocolonialism: When Technology for Good is Harmful*. Polity Books, 2025.
- Taylor, Linnet. “Public Actors Without Public Values: Legitimacy, Domination and the Regulation of the Technology Sector.” *Philosophy & Technology* 34 (2021), 897.

### Madianou-related conceptual reading

- Michael Power, work on audit.
- Caitlin Rosenthal, work referenced in relation to audit.
- Ellen Meiksins Wood, work referenced for the origins / relations of production framing of capitalism.
- Katharina Pistor, *The Code of Capital* / legal-regime framing referenced in Lecture 2.
- Bowker, Geoffrey C. and Susan Leigh Star. *Sorting Things Out: Classification and Its Consequences*.
- Tiqqun, *The Cybernetic Hypothesis*.

### Sen and entitlement approach

- Amartya Sen. “Food, Economics, and Entitlements,” chapter referenced in Lecture 2, pp. 34–52. DOI shown in slides: https://doi.org/10.1093/acprof:oso/9780198286356.003.0002

### Anticipatory Action and South Sudan

- Anticipation Hub: https://www.anticipation-hub.org
- Eason-Calabria. *Acting in Advance of Flooding: Early action in South Sudan* (2023). https://fic.tufts.edu/wp-content/uploads/05.10.23-ActingInAdvanceFinal.pdf
- Chavez-Gonzalez et al. *Anticipatory action: Lessons for the future* (2022).
- Parodi. *Anticipatory action for drought in the Sahel: an innovation for drought risk management or a buzzword?* (2024).
- Letz & Maxwell. *Anticipating, Mitigating, and Responding to Crises: How Do Information Problems Constrain Action?* https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4043459
- Breugen et al. *Equity in Health and Humanitarian Logistics: A People-Centered Perspective*. https://journals.sagepub.com/doi/10.1177/10591478241248751
- Weiffen et al. *Cash and Cohesion in Crisis: On the Impacts of Anticipatory Cash Transfers in IDP Camps in South Sudan during Floods*. https://hicn.org/wp-content/uploads/2025/08/HiCN-WP-433.pdf
- Hassan, Stites, Howe. *Pastoralists’ Perspectives on Early Warning, Anticipatory Action, and Emergency Response* (2024). https://fic.tufts.edu/wp-content/uploads/Desk_Study1_Pastoralist_Perspectives.pdf

### Additional resources listed in Lecture 3

- IPC Technical Manual: https://www.ipcinfo.org/fileadmin/user_upload/ipcinfo/manual/IPC_Technical_Manual_3_Final.pdf
- PhD thesis listed by Oxford Research Archive: https://ora.ox.ac.uk/objects/uuid:fb6b0bda-3818-4e38-8966-59974e32e690/files/dw3763760g
- Weingärtner. *Anticipatory crisis financing and action: concepts, initiatives, and evidence*.
- Further Weingärtner material on anticipatory action for livelihood protection.
- Historical analysis of the impacts of floods on agriculture in Sudan, FAO Open Knowledge.
- *Toolkit for anticipatory action in fragile, conflict- and violence-affected settings*.
- *Implementing Anticipatory Actions in Fragile, Conflict, and Migration Contexts: A Review of Global Lessons*.

---

## 23. Boundaries of what is covered in the provided lectures

The slides provide substantial social, ethical, political-economy, and humanitarian-governance material. They do **not** provide a detailed standalone legal compliance framework, a list of specific statutes, or a full treatment of Madianou’s logic of resistance. Those topics should therefore not be filled in from general knowledge if the assignment is meant to stay grounded in the supplied lecture material.

The strongest recurring message across all three lectures is that a technically successful model can still be socially, legally, or ethically problematic if it misdefines the problem, excludes people, reproduces inequities, creates surveillance or dependency, distorts accountability, ignores entitlements and markets, or treats data as self-explanatory.
