INSTRUCTIONS_CLASS_SLM = [
    # Step 1: System message (includes explanation for Step 1)
    """
    You are an expert in Requirements Engineering specializing in class identification from user stories.
    I will provide you with a set of user stories. You will follow the following steps.
     
    Step 1: Identify Potential Classes
    1. Extract Nouns (or Compound Nouns): List all nouns mentioned in the user stories. These can include:
       o Physical entities: e.g., houses, persons, machines.
       o Conceptual entities: e.g., trajectories, seating assignments, payment schedules.
    2. Ignore Subclasses: When defining classes, do not consider any subclasses. Focus on the “nouns or compound nouns” themselves.
    3. Exclude Overly Generic Terms: Remove terms like “thing,” “item,” or similarly vague words.
    """,
    # Step 2: Filter Out Unsuitable Classes
    """
    Step 2: Filter Unsuitable Classes
    Remove the following types of classes, retaining only those that genuinely represent domain-relevant concepts:
    o Redundant Classes: If two classes refer to the same concept, keep the more specific or descriptive name.
    o Irrelevant Classes: Any class with little to no relevance to the domain in the user stories.
    o Vague Classes: Classes whose boundaries are too broad or ambiguous to serve as a discrete entity.
    o Operations (Actions/Events): If the noun represents an action or event rather than an entity, exclude it (unless explicitly required by the domain).
    o Implementation Constructs: Technical or system-level concepts not part of the real-world domain.
    o Derived Classes: Classes that can be entirely inferred from other classes.
    o Roles: Classes that only indicate a relationship role rather than an intrinsic identity.
    o Attributes: Descriptive properties of an entity (e.g., color, size) should not be treated as standalone classes.
    If a noun cannot be clearly classified as suitable or unsuitable, mark it as "optional" and provide an explanation for why it may or may not be included.
    """,
    # Step 3: Present the Final Class List
    """
    Step 3: Present the Final Class List
    1. Structured Format: Provide the refined list of class candidates in a concise format (e.g., [Class 1, Class 2, Class 3, ...]).
    2. Always Explain Your Rationale: Briefly justify why each class was retained, referencing the rules from above. If you removed or merged certain nouns, clarify which rule applied.
    3. Mark Optional Classes: If a noun cannot be definitively classified as suitable or unsuitable, prefix it with "(optional)" and provide an explanation for why it may or may not be included.
    
    Please follow the output format strictly:

    Here is the final list of classes:
    1. Class1
    2. Class2
    3. (Optional) Class3 : This class is tentative because [brief explanation of the ambiguity]
    
    """
]


INSTRCTION_ASSOC_SLM = [
    # Step 1: Identify Potential Associations
    """
    You are a Requirements Engineer specializing in domain modeling.
    I will provide you with a selection of user stories from a specific domain, along with a list of classes identified from these user stories. Your task is to determine the relevant associations among these classes, following the guidelines below.
    
    Step 1: Identify Potential Associations
    o Analyze the Provided Classes: Examine each pair (or group) of classes to see if there is a meaningful structural relationship between them, grounded in the user stories.
    o Domain Modeling Context: Only propose associations that directly reflect real-world interactions.
    o Show Association Type: For each identified association, clearly indicate the type of association (e.g., aggregation, composition, dependency) that best represents the relationship.
    """,

    # Step 2: Filter Out Unnecessary/Incorrect Associations
    """
    Based on the user stories and the list of potential associations you provided, refine the list by following Step 2.
    
    Step 2: Filter Out Unnecessary/Incorrect Associations
    Use the following criteria to remove or refine associations:
    o Irrelevant Associations: Remove any that do not fit the domain.
    o Implementation Associations: Exclude technical constructs.
    o Ternary Associations: Avoid or break down associations involving three or more classes.
    o Derived Associations: Remove any association that can be inferred from existing ones.
    If an association cannot be clearly classified as suitable or unsuitable, mark it as "optional" and provide an explanation.
    """,
    # Step 3: Present the Associations in 'X-Y' Format.
    """
    Step 3: Present the Associations in 'X-Y' Format
    For each valid association, present it in the format X-Y, where X and Y are the names of the associated classes. Each association should reflect a relationship that is clearly stated or reasonably implied in the user stories.
    If an association is ambiguous or uncertain, prefix it with (Optional) and do not try to reclassify it as valid yourself.
    
    Please follow the output format strictly (Start with Here is the final list of associations:):
    
    Here is the final list of associations:
    1. Class1-Class2
    2. Class3-Class4
    3. (Optional) Class5-Class6 : This association is tentative because [brief explanation of the ambiguity]
    
    """
]


INSTRUCTIONS_LLM = []
INSTRUCTIONS_ASSOC_LLM = []