Insurance Claim Fraud Detection Using Machine
Learning
Lau Zhi Yi Sathiapriya Ramiah
Asia Pacific University of Asia Pacific University of
Technology and Innovation (APU) Technology and Innovation (APU)
Kuala Lumpur, Malaysia Kuala Lumpur, Malaysia
tp059579@mail.apu.edu.my sathiapriya@apu.edu.my
Abstract—Autoinsuranceclaimfraudhasbecomeincreasingly management, subrogation, process optimization, and fraud
prevalent in recent years posing a significant challenge for the detection [3]. By leveraging machine learning techniques, a
auto insurance industry. To address this issue there is a growing
robust model for detecting fraudulent auto insurance claims
need for more effective strategies to combat auto insurance
can be constructed and integrated into insurance claim fraud
claim fraud. The objective of this research is to utilize machine
learning techniques to develop an accurate model for detecting detection systems, thereby reducing the number of fraudu-
fraudulent auto insurance claims. By leveraging the power of lent claims. There are numerous machine learning techniques
machine learning, this research assists insurance professionals available globally, each with its own strengths and suitability
in determining whether an insurance claimant has engaged in
for different circumstances. The choice of machine learning
fraudulent activities related to vehicle insurance. The effective-
technique depends on the characteristics of the dataset. As
ness of classifier models K-Nearest Neighbors, Support Vector
Machines and Random evaluated by their accuracy, precision, the developer possesses a labeled dataset, supervised learning
recall and F1 score. Python programming language was used classificationtechniquesareappropriateforthisproject.Three
to facilitate the implementation of machine learning algorithms classification techniques, namely SVM, Random Forests, and
andthedevelopmentofuser-friendlywebapplications.Inconclu-
KNN, will be implemented in this research[41-42]. The aim
sion, RF outperformed other models with the highest accuracy,
ofthisresearchistodevelopanaccurateautoinsuranceclaim
precision, recall, and F1-score, contributing to improved fraud
detection and providing insurance companies with an effective frauddetectionsystemusingmachinelearningmodelsandaid
tool to reduce financial losses and uphold operational integrity. insurance companies in predicting potential insurance claim
Index Terms—Auto Insurance Claim, Fraud Detection, Data fraudandtakingappropriateactions.Byutilizingthepowerof
Analytics, Machine Learning Techniques, Classification Models
machine learning algorithms and addressing the challenges of
imbalanced datasets, the system will enhance fraud detection
I. INTRODUCTION
capabilities, reduce financial losses, and contribute to the
Insurance operates on the principle of mutual benefit, pro-
overall stability and integrity of the insurance industry. .
viding protection against large and unforeseen losses [1]. In
recent years, there has been a significant increase in public II. LITERATUREREVIEW
demand for insurance claims. However, insurance fraud poses
Auto insurance is one type that protects vehicle owners
athreattothissystem[1].Deliberatedeceitaimedatinsurance
by providing coverage for accidents, accidental damage, or
companies or agents for financial gain, insurance fraud has
theft,therebyalleviatingtheirfinancialburden[4].Whileauto
garneredsignificantattentionfromgovernments,societies,and
insurance offers numerous benefits, some individuals exploit
businesses in recent years [2]. Auto insurance fraud accounts
flaws in the insurance claim system to commit insurance
for approximately 80 percent of all insurance fraud cases [2].
fraud. Fraudulent claims have been a longstanding challenge
It not only infringes upon the rights of ordinary insurance
for insurance companies [5]. Notably, auto insurance fraud
consumersbutalsodisruptsthenormalfunctioningoftheauto
accountsforapproximately80percentofinsurancefraudcases
insurance market and jeopardizes road safety. Therefore, it is
[2]. Auto insurance fraud can take various forms, ranging
the responsibility of all stakeholders to establish an effective
fromsubmittingfakedocumentstostagingfictitiousaccidents
insuranceclaimsfrauddetectionsystemtomitigatetheoccur-
or auto thefts [6]. Detecting these fraudulent claims poses a
rence of such fraudulent cases. To develop a highly accurate
significant challenge for insurance companies, as the schemes
fraud detection system, machine learning techniques can be
becomeincreasinglysophisticated.Autoinsuranceclaimfraud
applied.Machinelearninghasthepotentialtoprovidesuperior
leads to substantial losses for insurance companies each year,
predictive accuracy and can be applied across the insurance
affecting not only them but also the individuals involved
value chain to identify risks, claims, and customer behaviors
in car insurance [5]. In the United States, insurance claims
[3]. It offers a wide range of applications in insurance,
fraud ranks as the second-largest white-collar crime, resulting
includingriskassessment,premiumleakagedetection,expense
in over 80 billion dollar in annual losses [7]. To offset
979-8-3315-3821-7/25/$31.00©2025IEEE these losses, insurance companies often pass on the costs to
01669111.5202.41226CTCMCI/9011.01
:IOD
|
EEEI
5202©
00.13$/52/7-1283-5133-8-979
| )CTCMCI(
gnitupmoC
ni
sdnerT
tnerruC
dna
esrevateM
no
ecnerefnoC
lanoitanretnI
5202
Authorized licensed use limited to: Jain University. Downloaded on March 06,2026 at 05:00:19 UTC from IEEE Xplore. Restrictions apply.

customers through higher insurance premiums [8], leading to Month Claimed: The months of January, May, October,
•
increasedfinancialburdensforpolicyholders.Recognizingthe and November are the ones where fraudulent claims are
need to combat insurance fraud, some insurance companies most likely to be made.
| have invested    | in the | development | of  | detection | systems using |               |                |          |            |        |       |
| ---------------- | ------ | ----------- | --- | --------- | ------------- | ------------- | -------------- | -------- | ---------- | ------ | ----- |
|                  |        |             |     |           |               | A. Imbalanced | Dataset        |          |            |        |       |
| machine learning |        | techniques. |     |           |               |               |                |          |            |        |       |
|                  |        |             |     |           |               | Fig. 1 shows  | that a dataset | that has | a majority | class, | which |
III. METHODOLOGY isaclassthathasmanymoreexampledistributionsthanother
Insurance companies can use some criteria to identify classes, is said to be imbalanced. This poses a challenge for
potential insurance claim fraud. According to the [9], the re- training classifiers in data mining and classification problems,
searchershaveanalyzedarealdatasetofautoinsurancefraud.
|     |     |     |     |     |     | as many algorithms | struggle | to handle | imbalanced | class | dis- |
| --- | --- | --- | --- | --- | --- | ------------------ | -------- | --------- | ---------- | ----- | ---- |
The researchers have established criteria to identify insurance tributions. Imbalanced datasets commonly occur in various
claim fraud from the dataset, including claim characteristics, real-life scenarios such as spam detection, credit card fraud
car type, policy type, and demographic characteristics. Each detection, and natural disaster detection [10]. In this research,
criterion has several variables in the dataset: the dataset is collected from “Angoss Knowledge Seeker”
Demographic characteristics: software, which has a dataset of auto insurance records in
Accident Area: Urban regions seem to be where fraudu- the United States from 1994 to 1996 [5]. It exhibits an
•
lent claims predominate. imbalanced distribution, with a majority of non-fraud cases
• Sex: Comparison with women, men commit fraud much (14,497)andaminorityoffraudcases(923).Toovercomethe
more frequently. imbalanced dataset problems, the developer can use multiple
datasamplingtechniquestoavoidbiasinthedata[11].Under-
| • Year: | Fraudulent | claims      | are more | likely to | occur in the   |     |     |     |     |     |     |
| ------- | ---------- | ----------- | -------- | --------- | -------------- | --- | --- | --- | --- | --- | --- |
| first   | two years  | than later. |          |           |                |     |     |     |     |     |     |
| Age     | of Driver: | Younger     | drivers  | (under 36 | years old) are |     |     |     |     |     |     |
•
| more    | likely to | commit        | fraud. |              |         |     |     |     |     |     |     |
| ------- | --------- | ------------- | ------ | ------------ | ------- | --- | --- | --- | --- | --- | --- |
| Address | Change:   | Policyholders |        | who recently | changed |     |     |     |     |     |     |
•
| their | address | are more | likely to | commit fraud. |     |     |     |     |     |     |     |
| ----- | ------- | -------- | --------- | ------------- | --- | --- | --- | --- | --- | --- | --- |
• Fault:Thepolicyholderismorelikelytobedishonestand
| committed   | in              | fraudulent    |         |          |                 |     |     |     |     |     |     |
| ----------- | --------------- | ------------- | ------- | -------- | --------------- | --- | --- | --- | --- | --- | --- |
| • Number    | of Supplements: |               | There   | are more | likely to be no |     |     |     |     |     |     |
| supplements |                 | in fraudulent | claims. |          |                 |     |     |     |     |     |     |
• PoliceReportFiled:Mostfraudulentclaimsdonotreport
to police.
| Vehicle | Type:    |            |         |              |         |     |     |     |     |     |     |
| ------- | -------- | ---------- | ------- | ------------ | ------- | --- | --- | --- | --- | --- | --- |
| • Make: | The most | fraudulent | claims  | typically    | pertain | to  |     |     |     |     |     |
| cars    | made by  | Honda,     | Toyota, | and Pontiac. |         |     |     |     |     |     |     |
AgeofVehicle:Peopleowningoldervehicles(thosewith
•
| vehicles   | 5 years   | old or | older)   | are more likely | to commit    |     |     |     |     |     |     |
| ---------- | --------- | ------ | -------- | --------------- | ------------ | --- | --- | --- | --- | --- | --- |
| fraudulent | claims.   |        |          |                 |              |     |     |     |     |     |     |
| Vehicle    | Category: | Sedan  | vehicles | are more        | likely to be |     |     |     |     |     |     |
•
| involved | in insurance |           | claim fraud. |        |                |     |     |     |     |     |     |
| -------- | ------------ | --------- | ------------ | ------ | -------------- | --- | --- | --- | --- | --- | --- |
| Vehicle  | Price:       | Low value | vehicles     | (under | 30,000 dollar) |     |     |     |     |     |     |
•
| are more | likely | involved | in insurance | claim | fraud. |     |     |     |     |     |     |
| -------- | ------ | -------- | ------------ | ----- | ------ | --- | --- | --- | --- | --- | --- |
Policy Type:
| Base | Policy: | In contrast | to liabilities, | fraudulent | claims |     |     |     |     |     |     |
| ---- | ------- | ----------- | --------------- | ---------- | ------ | --- | --- | --- | --- | --- | --- |
•
| are more    | likely | to be          | of the Collision | or All       | Perils type. |     |     |     |     |     |     |
| ----------- | ------ | -------------- | ---------------- | ------------ | ------------ | --- | --- | --- | --- | --- | --- |
| • Agent     | Type:  | It is more     | likely that      | the external | agent will   |     |     |     |     |     |     |
| be involved | in     | the fraudulent | claim.           |              |              |     |     |     |     |     |     |
Fig.1. Over-SamplingandUnder-SamplingwithImbalancedDataset[12]
Claim Characteristics:
• PastnumberofClaims:Fraudulentclaimstendtohappen sampling is removal of majority datasets either by using
to people who have a history of 2 to 4 past claims. statisticaltechniquesandrandomly.Meanwhile,over-sampling
• Deductible: Compared to claims with deductibles of any is produced more datasets based on the minority class by
other denomination, fraudulent claims with deductibles usingstatisticaltechniques[13].Todealwithimbalanceddata,
of 400 dollar are much more prevalent. under-sampling and over-sampling techniques are frequently
• Week of MonthClaimed: The middle of the monthtends utilized in ensemble learning or single model classifiers [12].
to be when the most fraudulent claims are filed. According to [5], the researchers encountered the issue of
• Month: The months which has the most accidents. an imbalanced dataset in the collected data. To address this
Authorized licensed use limited to: Jain University. Downloaded on March 06,2026 at 05:00:19 UTC from IEEE Xplore.  Restrictions apply.

problem,theyemployedtheSyntheticMinorityOversampling claim fraud, SVM can be employed to differentiate between
Technique (SMOTE), which is a popular data sampling tech- fraudulent and non-fraudulent insurance claims.
nique [14]. SMOTE is an algorithm that tackles imbalance by 2) K-Nearest Neighbor: K-Nearest Neighbors (KNN) is a
generating synthetic observations based on existing minority type of non-parametric classification algorithm [20]. The new
observations, randomly selected from the k-nearest neighbors unlabeled data is classified by figuring out which classes its
[15].Inthisstudy,SMOTEwasutilizedtoincreasethenumber neighbors are a part of [21]. This idea applied in the calcula-
of instances in the imbalanced dataset from 15,420 to 16,343, tion of the KNN algorithm, which allows us to classify tuples
resulting in the creation of a new balanced dataset. As the by fixing a particular value of K [21] Shown in Fig. 3. The
| result of | this study, | the | researchers | applied | the | classification |     |     |     |     |     |     |     |
| --------- | ----------- | --- | ----------- | ------- | --- | -------------- | --- | --- | --- | --- | --- | --- | --- |
techniquetothebalanceddataset,with93.72percentaccuracy
| for correct | classification. |            |     |     |     |     |     |     |     |     |     |     |     |
| ----------- | --------------- | ---------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B. Machine  | Learning        | Techniques |     |     |     |     |     |     |     |     |     |     |     |
Machinelearningreferstoatypeofcomputerprogramthat
| can learn   | on its   | own without | requiring   | explicit    |          | programming  |     |     |     |     |     |     |     |
| ----------- | -------- | ----------- | ----------- | ----------- | -------- | ------------ | --- | --- | --- | --- | --- | --- | --- |
| by a person | [16].    | In modern   | times,      | the term    | ”machine | learn-       |     |     |     |     |     |     |     |
| ing” is     | commonly | used        | to describe | a           | variety  | of programs  |     |     |     |     |     |     |     |
| used in     | big data | analytics   | and         | data mining |          | [16]. Unlike |     |     |     |     |     |     |     |
traditionalprogramming,machinelearningenablessystemsto
| automatically | learn     | from      | data and | adapt   | their behaviours[17]. |            |     |     |     |     |     |     |     |
| ------------- | --------- | --------- | -------- | ------- | --------------------- | ---------- | --- | --- | --- | --- | --- | --- | --- |
| Within the    | insurance | industry, |          | machine | learning              | can be im- |     |     |     |     |     |     |     |
Fig.3. K-NearestNeighbour(KNN)[22]
| plemented   | to        | develop a | system   | to detect | fraudulent | claim        |           |           |       |           |     |      |             |
| ----------- | --------- | --------- | -------- | --------- | ---------- | ------------ | --------- | --------- | ----- | --------- | --- | ---- | ----------- |
|             |           |           |          |           |            |              | K-Nearest | Neighbour | (KNN) | algorithm | has | been | extensively |
| activities. | To create | a highly  | accurate | insurance |            | claims fraud |           |           |       |           |     |      |             |
detectionsystem,machinelearningtechniquescanbeutilized. studied in the field of fraud detection to assist industries in
|         |          |         |           |       |         |            | reducing | costs associated |     | with fraudulent |     | activities. | In a study |
| ------- | -------- | ------- | --------- | ----- | ------- | ---------- | -------- | ---------------- | --- | --------------- | --- | ----------- | ---------- |
| Machine | learning | has the | potential | to be | applied | throughout |          |                  |     |                 |     |             |            |
the insurance value chain, including risk identification, claims conductedby[23],theresearchersutilizedtheKNNalgorithm
assessment, and analysis of customer behaviours, due to its todevelopacreditcardfrauddetectionmodel.Thefindingsof
|          |            |          |      |                  |     |            | the study | revealed | that methods |     | utilizing | the KNN | algorithm |
| -------- | ---------- | -------- | ---- | ---------------- | --- | ---------- | --------- | -------- | ------------ | --- | --------- | ------- | --------- |
| superior | predictive | accuracy | [3]. | The applications |     | of machine |           |          |              |     |           |         |           |
learning in insurance span various areas, such as assessing achieved an accuracy greater than 94.3 percent. On the other
|     |     |     |     |     |     |     | hand, the | two methods |     | with the | lowest | accuracy | were not |
| --- | --- | --- | --- | --- | --- | --- | --------- | ----------- | --- | -------- | ------ | -------- | -------- |
risktolerance,preventingpremiumlosses,managingexpenses,
handling subrogation, optimizing processes, and detecting related to the KNN algorithm.
fraudulent behaviours [3]. 3) Random Forest: Random forest is a mixture of tree
|                          |     |     |                             |     |     |     | predictors | where | each tree | depends | on the | value | of a random |
| ------------------------ | --- | --- | --------------------------- | --- | --- | --- | ---------- | ----- | --------- | ------- | ------ | ----- | ----------- |
| 1) SupportVectorMachine: |     |     | SupportVectorsaretheclosest |     |     |     |            |       |           |         |        |       |             |
data points or vectors to the hyperplane and have the greatest vector [24]. In a random forest, each tree predictor is a deci-
|           |          |     |            |     |          |            | sion tree. | The data | from | the available | datasets |     | are randomly |
| --------- | -------- | --- | ---------- | --- | -------- | ---------- | ---------- | -------- | ---- | ------------- | -------- | --- | ------------ |
| influence | on where | the | hyperplane | is  | located. | Hyperplane |            |          |      |               |          |     |              |
is the best boundary in the SVM shown in Fig. 2. In the chosen to create each decision tree. By randomly choosing
thecharacteristicsofthedecisiontree,thecorrelationbetween
treeswillbereducedtoincreaseaccuracyandefficiencyofthe
|     |     |     |     |     |     |     | prediction      | model       | shown          | in Fig.     | 4.          |       |                 |
| --- | --- | --- | --- | --- | --- | --- | --------------- | ----------- | -------------- | ----------- | ----------- | ----- | --------------- |
|     |     |     |     |     |     |     | Random          | Forest      | has been       | extensively | studied     |       | in the field of |
|     |     |     |     |     |     |     | fraud detection | to          | aid industries |             | in reducing | costs | associated      |
|     |     |     |     |     |     |     | with fraudulent | activities. |                | In a study  | conducted   |       | by [5], the re- |
searchersutilizedtheRandomForestClassificationTechnique
|     |     |     |     |     |     |     | to develop | a procedure |     | for identifying |     | auto-fraud | insurance |
| --- | --- | --- | --- | --- | --- | --- | ---------- | ----------- | --- | --------------- | --- | ---------- | --------- |
cases.
|     |     |     |     |     |     |     | C. Evaluation | Metrics |          |        |        |            |         |
| --- | --- | --- | --- | --- | --- | --- | ------------- | ------- | -------- | ------ | ------ | ---------- | ------- |
|     |     |     |     |     |     |     | 1) Accuracy:  |         | Accuracy | refers | to the | percentage | of data |
Fig.2. SupportVectorMachine[18] classified accurately in a dataset and correctly predicted out-
|     |     |     |     |     |     |     | puts. It is | calculated | by  | dividing | the total | number | of obser- |
| --- | --- | --- | --- | --- | --- | --- | ----------- | ---------- | --- | -------- | --------- | ------ | --------- |
field of fraud detection, Support Vector Machines (SVM) vations used for classification by the number of observations
have been extensively studied to assist industries in reducing that were correctly classified . Below is the accuracy formula
| costs associated |     | with fraudulent |     | activities. | For instance, | SVM | shown in | Fig. 5 : |     |     |     |     |     |
| ---------------- | --- | --------------- | --- | ----------- | ------------- | --- | -------- | -------- | --- | --- | --- | --- | --- |
can learn to recognize fraudulent credit card transactions by 2) Precision: Precisionreferstotheproportionofcorrectly
analyzing numerous records of both fraudulent and legitimate identified outputs, or the exactness of the model. Below is the
credit card activity [19]. Similarly, in the case of insurance precision formula Fig. 6:
Authorized licensed use limited to: Jain University. Downloaded on March 06,2026 at 05:00:19 UTC from IEEE Xplore.  Restrictions apply.

Fig.6. Precision
Fig.7. Recall
The experimental results demonstrate the superiority of the
Fig.4. RandomForest SMOTEwithRandomForestapproachinautoinsuranceclaim
fraud detection. The proposed method achieved the highest
Accuracy, Precision, and F1 score compared to the alternative
classification techniques, with 96.74percent, 98.72 percent,
and 96.70 percent. The performance evaluation reveals that
Fig.5. Accuracy the SMOTE with Random Forests model outperforms both
SMOTEwithK-NearestNeighborsandSMOTEwithSupport
VectorMachinesinidentifyingfraudulentclaims,thusoffering
3) Recall: Recall is the percentage of observations that
a more reliable and efficient solution to combat fraud in the
belong to a given class that the model correctly classified.
auto insurance domain.
Below is the recall formula Fig. 7:
4) F1Score: F1scoreistheaverageofprecisionandrecall. V. CONCLUSION
F1 considers both false positive and false negative, whereas
In conclusion, the development of an accurate auto insur-
precision only consider false positive and recall only consider
ance claim fraud detection system using machine learning
falsenegative,respectively.Whenclassdistributionisuneven,
techniques is crucial to address the increasing issue in in-
F1 is highly helpful. Below is the F1 score formula Fig. 8:
surance fraudulent activities. Insurance fraud, especially in
IV. RESULTANDDISCUSSION auto insurance, not only impacts insurance companies but
also affects the rights of consumers and road safety. By
In this research, the researcher proposed SMOTE as an
incorporating machine learning algorithms, a robust model
oversampling method to address the issue of class imbalance
can be constructed and integrated into insurance claim fraud
within the researcher’s collected dataset.
Fig. 9 illustrates the distribution of the “FraudFound P ” detection systems to reduce the number of fraudulent claims.
variable, indicating a higher count of “0” compared to ”1,” This research paper presents a comprehensive investigation
suggestingalowerlikelihoodoffraud.Thegraphhighlightsan into auto insurance claim fraud detection emphasizing the
imbalanced class label. Conversely, Figures 10 illustrates the effectiveness of SMOTE combined with Random Forest. By
distributionofthe“FraudFound P”variableafterapplyingthe
SMOTE technique. In contrast to Figure 9, the counts of “0”
TABLEI
and“1”arenowequal,indicatinga50percentchanceoffraud
COMPARISONOFMACHINELEARNINGMODELSONPERFORMANCE
occurrence. Moreover, the graph demonstrates the successful METRICS
resolution of the data imbalance issue. Once the imbalanced
data issue was addressed, the researcher employed the Ran- Metric SVM Random KNN Best
For- Score
dom Forest classification technique to detect fraud in auto
est
insurance claims. In addition, other classification techniques,
Accuracy 84.31 96.74 93.14 Random
namely K-Nearest Neighbors and Support Vector Machines, Forest
were compared. Following the completion of development, Precision 81.03 98.72 91.05 Random
the developers utilized evaluation metrics such as Accuracy, Forest
Precision, Recall, and F1 score to compare the performance Recall 89.90 94.76 95.79 K-
Nearest
ofthethreeclassifiermodels.Thefollowingtabledisplaysthe
Neigh-
comparison of the model’s performance. The Table 1 shows bour
the comparison of Machine Learning Models on Performance F1 85.24 96.70 93.36 Random
Metrics. Score Forest
Authorized licensed use limited to: Jain University. Downloaded on March 06,2026 at 05:00:19 UTC from IEEE Xplore. Restrictions apply.

[6] E.W.T.Ngai,Y.Hu,Y.H.Wong,Y.Chen,andX.Sun,“Theapplication
ofdataminingtechniquesinfinancialfrauddetection:Aclassification
|     |     |     |     |     | framework | and | an academic | review | of  | literature,” | Decis Support | Syst, |
| --- | --- | --- | --- | --- | --------- | --- | ----------- | ------ | --- | ------------ | ------------- | ----- |
vol.50,no.3,pp.559–569,2011,doi:10.1016/j.dss.2010.08.006.
|     |     |     |     |     | [7] Corum, | “Insurance | Research    |        | Council   | Finds That  | Fraud and            | Buildup |
| --- | --- | --- | --- | --- | ---------- | ---------- | ----------- | ------ | --------- | ----------- | -------------------- | ------- |
|     |     |     |     |     | Add        | Up to      | 7.7 Billion | dollar | in Excess | Payments    | for Auto             | Injury  |
|     |     |     |     |     | Claims,”   | Insurance  | Research    |        | Council,  | p. 3, 2015, | [Online]. Available: |         |
www.insurance-research.org,
Fig.8. F1score[30] [8] S. Viaene and G. Dedene, “Insurance Fraud: Issues and Challenges,”
GenevaPapersonRiskandInsurance:IssuesandPractice,vol.29,no.
2,pp.313–333,2004,doi:10.1111/j.1468-0440.2004.00290.x.
|     |     |     |     |     | [9] C. A. | Hargreaves |     | and V.       | Singhania, | “Analytics | for Insurance        |     |
| --- | --- | --- | --- | --- | --------- | ---------- | --- | ------------ | ---------- | ---------- | -------------------- | --- |
|     |     |     |     |     | Fraud     | Detection: |     | An Empirical |            | Study,”    | Files.Aiscience.Org, |     |
|     |     |     |     |     | vol.      | 1, no.     | 3,  | pp. 227–232, |            | 2015,      | [Online]. Available: |     |
http://files.aiscience.org/journal/article/pdf/70110035.pdf
|     |     |     |     |     | [10] H. Zhang, | Z.          | Li, H. | Shahriar,       | L. Tao,      | P. Bhattacharya, | and                | Y. Qian, |
| --- | --- | --- | --- | --- | -------------- | ----------- | ------ | --------------- | ------------ | ---------------- | ------------------ | -------- |
|     |     |     |     |     | “Improving     | prediction  |        | accuracy        | for logistic | regression       | on imbalanced      |          |
|     |     |     |     |     | datasets,”     | Proceedings |        | - International |              | Computer         | Software and       | Appli-   |
|     |     |     |     |     | cations        | Conference, | vol.   | 1, pp.          | 918–919,     | 2019,            | doi: 10.1109/COMP- |          |
SAC.2019.00140.
|     |     |     |     |     | [11] Insurance |     | Europe, |     | “The  | impact    | of         | in- |
| --- | --- | --- | --- | --- | -------------- | --- | ------- | --- | ----- | --------- | ---------- | --- |
|     |     |     |     |     | surance        |     | fraud,” |     | 2013, | [Online]. | Available: |     |
http://www.insuranceeurope.eu/sites/default/files/attachments/The
impactofinsurancefraud.pdf
[12] L.Zhang,T.Wu,X.Chen,B.Lu,C.Na,andG.Qi,“AutoInsurance
KnowledgeGraphConstructionandItsApplicationtoFraudDetection,”
ACMInternationalConferenceProceedingSeries,pp.64–70,2021,doi:
10.1145/3502223.3502231.
[13] R.D.Burri,R.Burri,R.R.Bojja,andS.R.Buruga,“Insuranceclaim
|     |     |     |     |     | analysis | using | machine | learning | algorithms,” | International | Journal | of  |
| --- | --- | --- | --- | --- | -------- | ----- | ------- | -------- | ------------ | ------------- | ------- | --- |
Fig.9. Distributionoftheclasslabel“FraudFound P”withoutusingSMOTE InnovativeTechnologyandExploringEngineering,vol.8,no.6Special
Issue4,pp.577–582,2019,doi:10.35940/ijitee.F1118.0486S419.
[14] D.K.PatelandS.Subudhi,“Applicationofextremelearningmachine
|     |     |     |     |     | in detecting |     | auto insurance | fraud,” | Proceedings |     | - 2019 International |     |
| --- | --- | --- | --- | --- | ------------ | --- | -------------- | ------- | ----------- | --- | -------------------- | --- |
conducting a comparative analysis with K-Nearest Neighbors Conference on Applied Machine Learning, ICAML 2019, pp. 78–81,
and Support Vector Machines, the researche has demonstrated 2019,doi:10.1109/ICAML48257.2019.00023.
[15] S.Harjai,S.K.Khatri,andG.Singh,“DetectingFraudulentInsurance
| the superiority | of the proposed | approach. |     | The research con- |        |       |        |         |               |          |              |     |
| --------------- | --------------- | --------- | --- | ----------------- | ------ | ----- | ------ | ------- | ------------- | -------- | ------------ | --- |
|                 |                 |           |     |                   | Claims | Using | Random | Forests | and Synthetic | Minority | Oversampling |     |
tributes to the advancement of fraud detection methodologies Technique,” 2019 4th International Conference on Information Sys-
in the auto insurance industry offering insurance companies tems and Computer Networks, ISCON 2019, pp. 123–128, 2019, doi:
10.1109/ISCON47742.2019.9036162.
a powerful tool to mitigate financial losses and maintain the [16] E.W.T.Ngai,Y.Hu,Y.H.Wong,Y.Chen,andX.Sun,“Theapplication
integrity of their operations. Future research directions may ofdataminingtechniquesinfinancialfrauddetection:Aclassification
involve exploring additional data preprocessing techniques framework and an academic review of literature,” Decis Support Syst,
vol.50,no.3,pp.559–569,2011,doi:10.1016/j.dss.2010.08.006.
| and incorporating | other advanced | or  | combination | of multiple |             |            |          |     |         |            |           |         |
| ----------------- | -------------- | --- | ----------- | ----------- | ----------- | ---------- | -------- | --- | ------- | ---------- | --------- | ------- |
|                   |                |     |             |             | [17] Corum, | “Insurance | Research |     | Council | Finds That | Fraud and | Buildup |
machinelearningalgorithmstofurtherenhancefrauddetection Add Up to 7.7 Billion dollar in Excess Payments for Auto Injury
|     |     |     |     |     | Claims,” | Insurance | Research |     | Council, | p. 3, 2015, | [Online]. Available: |     |
| --- | --- | --- | --- | --- | -------- | --------- | -------- | --- | -------- | ----------- | -------------------- | --- |
capabilities.
www.insurance-research.org,
|     |     |     |     |     | [18] S. Viaene | and | G. Dedene, | “Insurance |     | Fraud: Issues | and Challenges,” |     |
| --- | --- | --- | --- | --- | -------------- | --- | ---------- | ---------- | --- | ------------- | ---------------- | --- |
REFERENCES GenevaPapersonRiskandInsurance:IssuesandPractice,vol.29,no.
2,pp.313–333,2004,doi:10.1111/j.1468-0440.2004.00290.x.
|     |     |     |     |     | [19] C. A. | Hargreaves |     | and V. | Singhania, | “Analytics | for Insurance |     |
| --- | --- | --- | --- | --- | ---------- | ---------- | --- | ------ | ---------- | ---------- | ------------- | --- |
[1] Insurance Europe, “The impact of in- Fraud Detection: An Empirical Study,” Files.Aiscience.Org,
| surance | fraud,” | 2013, | [Online]. | Available: |      |        |     |              |     |       |                      |     |
| ------- | ------- | ----- | --------- | ---------- | ---- | ------ | --- | ------------ | --- | ----- | -------------------- | --- |
|         |         |       |           |            | vol. | 1, no. | 3,  | pp. 227–232, |     | 2015, | [Online]. Available: |     |
http://www.insuranceeurope.eu/sites/default/files/attachments/The
http://files.aiscience.org/journal/article/pdf/70110035.pdf
impactofinsurancefraud.pdf [20] H. Zhang, Z. Li, H. Shahriar, L. Tao, P. Bhattacharya, and Y. Qian,
[2] L.Zhang,T.Wu,X.Chen,B.Lu,C.Na,andG.Qi,“AutoInsurance “Improving prediction accuracy for logistic regression on imbalanced
KnowledgeGraphConstructionandItsApplicationtoFraudDetection,” datasets,” Proceedings - International Computer Software and Appli-
ACMInternationalConferenceProceedingSeries,pp.64–70,2021,doi: cations Conference, vol. 1, pp. 918–919, 2019, doi: 10.1109/COMP-
10.1145/3502223.3502231.
SAC.2019.00140.
[3] R.D.Burri,R.Burri,R.R.Bojja,andS.R.Buruga,“Insuranceclaim [21] S. Kandel, A. Paepcke, J. M. Hellerstein, and J. Heer, “Enterprise
analysis using machine learning algorithms,” International Journal of data analysis and visualization: An interview study,” IEEE Trans
InnovativeTechnologyandExploringEngineering,vol.8,no.6Special Vis Comput Graph, vol. 18, no. 12, pp. 2917–2926, 2012, doi:
Issue4,pp.577–582,2019,doi:10.35940/ijitee.F1118.0486S419. 10.1109/TVCG.2012.219.
[4] D.K.PatelandS.Subudhi,“Applicationofextremelearningmachine [22] M. Y. Arafat, S. Hoque, S. Xu, and D. M. Farid, “An under-sampling
in detecting auto insurance fraud,” Proceedings - 2019 International method with support vectors in multi-class imbalanced data classifi-
Conference on Applied Machine Learning, ICAML 2019, pp. 78–81, cation,” 2019 13th International Conference on Software, Knowledge,
2019,doi:10.1109/ICAML48257.2019.00023. InformationManagementandApplications,SKIMA2019,no.August,
[5] S.Harjai,S.K.Khatri,andG.Singh,“DetectingFraudulentInsurance pp.1–6,2019,doi:10.1109/SKIMA47702.2019.8982391.
Claims Using Random Forests and Synthetic Minority Oversampling [23] C. Muranda, A. Ali, and T. Shongwe, “Detecting Fraudulent Motor
Technique,” 2019 4th International Conference on Information Sys- Insurance Claims Using Support Vector Machines with Adaptive Syn-
tems and Computer Networks, ISCON 2019, pp. 123–128, 2019, doi: thetic Sampling Method,” 2020 61st International Scientific Confer-
10.1109/ISCON47742.2019.9036162. ence on Information Technology and Management Science of Riga
Authorized licensed use limited to: Jain University. Downloaded on March 06,2026 at 05:00:19 UTC from IEEE Xplore.  Restrictions apply.

Technical University, ITMS 2020 - Proceedings, pp. 0–4, 2020, doi:
10.1109/ITMS51158.2020.9259322.
[24] Z.Zheng,Y.Cai,andY.Li,“Oversamplingmethodforimbalancedclas-
sification,”ComputingandInformatics,vol.34,no.5,pp.1017–1037,
2015.
Authorized licensed use limited to: Jain University. Downloaded on March 06,2026 at 05:00:19 UTC from IEEE Xplore. Restrictions apply.
