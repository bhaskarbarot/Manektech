from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


# -----------------------------------------------------------------------------
# Query DTOs
# -----------------------------------------------------------------------------


class SearchRequest(BaseModel):
    """
    Competency search request with semantic similarity matching.
    
    The search uses vector embeddings to find competencies semantically similar to your query.
    Only 'query' is mandatory; all other fields are optional.
    
    Fields:
        query (required): Natural language search query (e.g., "probleemoplossend vermogen")
        limit (optional): Maximum number of results to return (default: 10)
        filters (optional): Filter results by attributes:
            - framework: "FGR" or "ESCO" (filter by competency framework)
            - class: "skill" or "competency" (filter by entity type, lowercase only)
        response_format (optional): "compact" (default) or "full" (includes all metadata)
    
    Available filter values:
        - framework: "FGR", "ESCO"
        - class: "skill", "competency" (must be lowercase)
    """

    query: str = Field(
        description="Natural language search query for finding competencies"
    )
    limit: Optional[int] = Field(
        default=10,
        description="Maximum number of results to return"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Filter results by framework (FGR/ESCO) or class (skill/competency, lowercase)"
    )
    response_format: Optional[str] = Field(
        default="compact",
        description="Response format: 'compact' (default) or 'full' (all fields)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "openapi_examples": {
                "quick_keyword_search": {
                    "summary": "Quick search (compact, defaults)",
                    "value": {"query": "data engineering"},
                },
                "focused_top_k": {
                    "summary": "Focused search with smaller limit",
                    "value": {"query": "vector search", "limit": 5},
                },
                "skills_filter": {
                    "summary": "Filter to skills only",
                    "value": {
                        "query": "programmeren",
                        "filters": {"class": "skill"},
                        "limit": 10
                    }
                },
                "framework_filter": {
                    "summary": "Framework filter (ESCO)",
                    "value": {
                        "query": "Python programmeren",
                        "filters": {"framework": "ESCO"},
                        "limit": 5,
                        "response_format": "full"
                    }
                },
            }
        }
    )


class SearchCompetencyRequest(SearchRequest):
    """
    Search for competencies using semantic similarity.
    
    This endpoint searches the competency ontology database using vector embeddings
    to find competencies that are semantically similar to your query.
    
    Usage:
        - Simple search: Just provide a query string
        - Framework-specific: Add filters with "framework": "FGR" or "ESCO"
        - Type-specific: Add filters with "class": "skill" or "competency" (lowercase)
        - Combined filters: Use multiple filters together
    
    Only 'query' is mandatory. All other parameters are optional.
    
    Available filter values:
        - framework: "FGR", "ESCO"
        - class: "skill", "competency" (lowercase only)
    
    Examples:
        1. Search FGR framework: {"query": "probleemoplossend vermogen", "filters": {"framework": "FGR"}, "limit": 5}
        2. Simple search: {"query": "analytisch redeneren"}
        3. Multiple filters: {"query": "leiderschap", "filters": {"framework": "FGR", "class": "competency"}}
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "openapi_examples": {
                "fgr_framework_filter": {
                    "summary": "Search FGR framework only (recommended example)",
                    "description": "Search for problem-solving competency in FGR framework",
                    "value": {
                        "query": "probleemoplossend vermogen",
                        "filters": {"framework": "FGR"},
                        "limit": 5
                    }
                },
                "esco_framework_filter": {
                    "summary": "Search ESCO framework only",
                    "description": "Search for analytical reasoning in ESCO framework",
                    "value": {
                        "query": "analytisch redeneren",
                        "filters": {"framework": "ESCO"},
                        "limit": 5
                    }
                },
                "query_only": {
                    "summary": "Simple search (query only)",
                    "description": "Simplest case - just a query, no filters",
                    "value": {"query": "stakeholdermanagement"}
                },
                "query_with_limit": {
                    "summary": "Query with custom limit",
                    "description": "Search with top 5 results only",
                    "value": {"query": "communicatieve vaardigheden", "limit": 5}
                },
                "full_response_format": {
                    "summary": "Full response with all metadata",
                    "description": "Get complete entity information including all fields",
                    "value": {
                        "query": "leiderschap",
                        "filters": {"framework": "FGR"},
                        "response_format": "full",
                        "limit": 10
                    }
                },
                "skills_only": {
                    "summary": "Filter by entity class (skills only)",
                    "description": "Search only skills (not competencies)",
                    "value": {
                        "query": "programmeren",
                        "filters": {"class": "skill"},
                        "limit": 10
                    }
                }
            }
        }
    )


class SearchOccupationRequest(SearchRequest):
    model_config = ConfigDict(
        json_schema_extra={
            "openapi_examples": {
                "query_only": {
                    "summary": "Query only (simplest case)",
                    "value": {"query": "data engineer"},
                },
                "query_only_variation": {
                    "summary": "Query only (another common role)",
                    "value": {"query": "business analist"},
                },
                "query_with_limit": {
                    "summary": "Query + limit (top 5)",
                    "value": {"query": "beleidsadviseur", "limit": 5},
                },
                "query_full_response": {
                    "summary": "Query + full response format",
                    "value": {
                        "query": "softwareontwikkelaar",
                        "response_format": "full",
                    },
                },
            }
        }
    )

# --------------------------------------------------------------------------------
# Skill Extraction DTOs
# --------------------------------------------------------------------------------
class VacancyTextRequest(BaseModel):
    """Request model for extracting skills from vacancy text with dual ESCO/FGR search."""

    Functietitel: str = Field(
        description="Job title for the vacancy"
    )
    vacancy_description: str = Field(
        description="Full description of the vacancy for skill extraction"
    )
    limit: Optional[int] = Field(
        default=3,
        description="Maximum number of matches to return per framework (ESCO/FGR) for each skill"
    )
    extraction_prompt: Optional[str] = Field(
        default=None,
        description="Optional custom prompt template for skill extraction. Use {job_title} and {vacancy_text} as placeholders."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "openapi_examples": {
                "Senior Java Developer": {
                    "summary": "Senior Java Developer vacancy with limit 3",
                    "value": {
                        "Functietitel": "Senior Java developer",
                        "vacancy_description": "Intro,De Belastingdienst beheert een van de grootste databanken van Europa met daarin de fiscale informatie van miljoenen burgers en bedrijven. Onze applicaties zijn van essentieel belang voor onze samenleving. Als senior Java-developer heb je een richtinggevende rol binnen het scrumteam waarmee je dagelijks, vanuit Apeldoorn, werkt aan deze applicaties. Wil je meer informatie over Java bij de Belastingdienst? Klik op deze speciale pagina,Dit doe je bij de..., Welke technologie kunnen we het beste inzetten voor de ontwikkeling van een applicatie? En als we een bepaald vraagstuk op meerdere manieren kunnen oplossen, welke kiezen we dan? Dat zijn de vraagstukken waarop jij je richt. Natuurlijk maak je deze complexe technische keuzes niet alleen. Je werkt nauw samen met de andere Java-experts in je team. Wel ben jij vervolgens degene die de knopen doorhakt. Je loopt voorop als gaat om het delen van kennis, en inspireert en coacht je collegas. Zo geef je workshops en presentaties aan Java-vakgenoten over de nieuwste toepassingen. Ook pak je een sleutelrol in de meetings van de Java-vakgroep waarin zo’n honderd Java-developers sparren over teamoverstijgende en vooruitstrevende projecten die voor de Belastingdienst van betekenis kunnen zijn. Via (inter)nationale events als J-Fall of Devoxx blijf je op de hoogte van ontwikkelingen en trends. Daarnaast neem je de regie in de transitie die onze IT-teams doormaken richting zelfsturende DevOps-teams. Hierbij zorg je dat onze teamst steeds meer verantwoordelijkheden naar zich toetrekken. Professionele ontwikkeling én optimale software: dat is jouw doel.,Een bijzondere baan, omdat..., je werk ontzettend divers is; er zijn altijd nieuwe vraagstukken en uitdagingen én we zijn continu op zoek naar verbetering. je in scrumteams samenwerkt in een professionele en tegelijkertijd informele werksfeer. Quote; dit zegt een collega over jouw werkomgeving,“In de Rotterdamse haven komen grote containerschepen binnen die diverse waren moeten aangeven. Zonder onze applicaties kunnen zij niets meer in- of uitvoeren. Er ontstaan dan bijvoorbeeld lange files van vrachtwagens die goederen willen ophalen. Ons werk is dus van maatschappelijk belang.” Bert, senior Javadeveloper bij de Belastingdienst. Wanneer past deze baan bij je? Je hebt hbo werk- en denkniveau. Je beschikt bij voorkeur over SCJP/OCPJP én een aantal aanvullende Java-certificaten, of je bent bereid deze te halen. Je hebt minimaal vijf jaar werkervaring met het ontwikkelen in Java Enterprise Edition en bent in staat mee te denken over de software-architectuur. Je beheerst diverse van de frameworks en tooling die wij gebruiken, onder meer Angular, Maven, OpenShift, Jenkins, SonarQube, Git en Jira. Je hebt brede kennis van continuous integration, continuous delivery, DevOps en containerhosting. Je hebt bij voorkeur ervaring met het geven van presentaties en workshops, en met het coachen van mensen. Jouw competenties, analyseren, samenwerken, klantgerichtheid, resultaatgerichtheid, plannen en organiseren,De afdeling,De directie Informatievoorziening is hét ICT-bedrijf van de Belastingdienst. Met ruim 3.000 collega’s zorgen we dat Nederland kan rekenen op betrouwbare informatievoorzieningen en ICT-systemen. Heel Nederland? Ja, onze ‘klanten’ zijn niet alleen Belastingdienstmedewerkers, maar ook 8.600 grote ondernemers, 2,2 miljoen mkb-ondernemers en 8,5 miljoen burgers. En wist je dat wij werken volgens een agile-mindset? Open,transparant en gericht op leren en kennis delen. Door de toepassing van een DevOps-werkwijze en ons aanbod van geautomatiseerde technieken kunnen de systemen van de Belastingdienst dagelijks miljoenen data en euro’s verwerken. Bij ons werk je in een moderne tech-organisatie met ménsen als kloppend hart. Of je nu als engineer of in een andere rol bijdraagt aan effectieve ICT; jouw inzet doet ertoe. Net als jouw ontwikkeling, waarin wij graag investeren. En jouw ideeën, waar we graag naar luisteren. Ook is er volop ruimte om samen te innoveren met externe partijen. Niet alleen om te moderniseren, maar vooral om nieuwe producten en diensten te ontwikkelen die passen bij de belevingswereld van burgers, bedrijven en collega’s. ,De organisatie,Bij de Belastingdienst werken ongeveer 25.000 mensen verspreid over het hele land aan een financieel gezond Nederland. Dit doen we door eerlijk en zorgvuldig belastingen en premies volksverzekeringen te heffen, te innen en te controleren en fraude op te sporen. De Belastingdienst maakt het burgers en bedrijven zo gemakkelijk mogelijk om verplichtingen na te kunnen komen en gebruik te kunnen maken van rechten. Dat gebeurt met passende dienstverlening, door massale processen juist en tijdig uit te voeren én door adequaat toezicht uit te oefenen. De Belastingdienst is sterk in ontwikkeling en heeft de ambitie om de beste Belastingdienst voor Nederland te zijn met focus op fiscale taken en vakmanschap. Lees meer over de Belastingdienst op: https://over-ons.belastingdienst.nl,Bijzonderheden, We ontvangen je brief en cv graag in een Word- of PDF-bestand. Neem in de bestandsnaam jouw voor- en achternaam op. Als je een beroep doet op een voorrangspositie, stuur dan ook een kopie van die kennisgeving mee.,De voorkeur gaat uit naar kandidaten die het meest aansluiten bij het opgestelde profiel. Dit heeft betrekking op zowel de genoemde kennis en werkervaring als op het opleidingsniveau. Vermeld deze daarom duidelijk in je cv. De Belastingdienst zet zich in voor de banenafspraak: zoveel mogelijk banen realiseren voor mensen met een arbeidsbeperking. Val jij in deze doelgroep? Wij zullen je ondersteunen zodat je optimaal kunt functioneren, en daarmee jouw bijdrage aan Nederland kunt leveren. Of het nu gaat om aanpassingen op je werkplek, bepaalde voorzieningen in het vervoer of bijvoorbeeld vergoedingen van het UWV: samen met jou, je leidinggevende én een jobcoach gaan wij kijken naar jouw kwaliteiten en mogelijkheden om een passend werkpakket uit te voeren. Wil jij weten of je hierbij hoort en wat dit exact betekent voor jou? Lees hier meer.,Een (online) voorselectietest en/of een assessment kan deel uit maken van de sollicitatieprocedure, evenals het maken van een casus, het opvragen van referenties en (online) screening, bijvoorbeeld via databanken,(zoekmachines) en sociale netwerken.,Jouw sollicitatie wordt alleen in behandeling genomen als je met de sollicitatie-button reageert en je cv en motivatiebrief zijn bijgesloten. Na sluitingsdatum is het niet meer mogelijk om je sollicitatie in behandeling te nemen. Houd er rekening mee dat het solliciteren technische problemen met zich mee kan brengen. Wacht hiermee dus niet tot het laatste moment. Wanneer je solliciteert op een functie maak je eenmalig een account aan. Met je account kan je de status van je sollicitatie inzien.,Salarisomschrijving,Inschaling vindt plaats in de bij de functie behorende salarisschaal. Bij het ontbreken van relevante kennis en ervaring kan tijdelijk een lagere salarisschaal worden toegepast. Overige arbeidsvoorwaarden,Naast salaris ontvang je ook een individueel keuzebudget (IKB). Jouw IKB bestaat uit geld (IKB-budget) en tijd (IKB-uren). Het IKB geeft je de mogelijkheid om naar eigen keuze een deel van je IKB-budget te laten uitbetalen op de door jou gekozen tijdstippen. Én je hebt de mogelijkheid om je IKB-budget deels om te zetten in verlof of andersom. Ook kun je het IKB-budget besteden aan een fiscaal-vriendelijk doel, zoals bijvoorbeeld een fiets, bedrijfsfitness of vakliteratuur. De Rijksoverheid hecht sterk aan persoonlijke groei en loopbaanontwikkeling en biedt daarvoor tal van mogelijkheden. Tot de secundaire arbeidsvoorwaarden behoren onder meer studiefaciliteiten, ouderschapsverlof en een vergoeding woon-werkverkeer. Wij verwachten van onze werknemers dat ze integer zijn en we vragen aan nieuwe medewerkers een Verklaring Omtrent Gedrag (VOG). Als deze niet kan worden overlegd, volgt geen arbeidsovereenkomst of wordt de arbeidsovereenkomst na uiterlijk 3 maanden beëindigd wanneer duidelijk is dat geen VOG overgelegd kan worden.",
                        "limit": 1
                    },
                },
                "Data Scientist": {
                    "summary": "Data Scientist vacancy with limit 5",
                    "value": {
                        "Functietitel": "Data Scientist",
                        "vacancy_description": "We zijn op zoek naar een ervaren Data Scientist om ons team te versterken. In deze rol ben je verantwoordelijk voor het analyseren van grote datasets, het ontwikkelen van voorspellende modellen en het vertalen van data-inzichten naar concrete aanbevelingen voor onze business. Je werkt nauw samen met verschillende teams, waaronder IT, marketing en sales, om data-gedreven beslissingen te ondersteunen. Vereisten: - 3+ jaar ervaring als Data Scientist - Sterke vaardigheden in Python en machine learning libraries (zoals scikit-learn, TensorFlow) - Ervaring met big data tools (zoals Hadoop, Spark) - Uitstekende communicatieve vaardigheden en stakeholder management - Kennis van DevOps-praktijken en CI/CD pipelines is een pluspunt - Teamspeler met een proactieve houding Competenties: - Analytisch denken - Resultaatgerichtheid - Samenwerken",
                        "limit": 3
                    },
                },
            }
        }
    )


# -----------------------------------------------------------------------------
# Result DTOs
# -----------------------------------------------------------------------------


class SearchResultCompact(BaseModel):
    class_: Optional[str] = Field(default=None, alias="class")
    framework: Optional[str] = None
    uri: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    similarity_score: Optional[float] = None

    model_config = ConfigDict(populate_by_name=True)


class SearchResultFull(BaseModel):
    id: Optional[str] = None
    class_: Optional[str] = Field(default=None, alias="class")
    framework: Optional[str] = None
    uri: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    group: Optional[str] = None
    subgroup: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    similarity_score: Optional[float] = None

    model_config = ConfigDict(populate_by_name=True)


class SearchResponse(BaseModel):
    results: List[Union[SearchResultCompact, SearchResultFull]]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "results": [
                        {
                            "class": "competency",
                            "framework": "FGR",
                            "uri": "http://example.org/fgr/competency/001",
                            "label": "probleemoplossend vermogen",
                            "description": "Het vermogen om problemen te analyseren en effectieve oplossingen te ontwikkelen.",
                            "similarity_score": 0.945
                        },
                        {
                            "class": "skill",
                            "framework": "ESCO",
                            "uri": "http://data.europa.eu/esco/skill/3a5231a0-8c30-48ee-b671-08e2debd4441",
                            "label": "organisatorisch beleid",
                            "description": "Beleid voor het bereiken van doelstellingen met betrekking tot ontwikkeling van een organisatie.",
                            "similarity_score": 0.899
                        }
                    ]
                }
            ]
        }
    )

# --------------------------------------------------------------------------------
# Skill Extraction Response DTOs
# --------------------------------------------------------------------------------

class ExtractedCompetency(BaseModel):
    """Single extracted competency match with flattened structure."""
    raw_mention: str = Field(description="Raw skill/competency text extracted from vacancy")
    class_: Optional[str] = Field(default=None, alias="class", description="Entity class (skill/competency)")
    uri: Optional[str] = Field(default=None, description="URI of the matched entity")
    title: Optional[str] = Field(default=None, description="Title/label of the matched entity")
    description: Optional[str] = Field(default=None, description="Description of the matched entity")
    similarity_score: Optional[float] = Field(default=None, description="Similarity score (0-1)")
    ontology: Optional[str] = Field(default=None, description="Ontology/framework name (esco or fgr)")

    model_config = ConfigDict(populate_by_name=True)


class SkillExtractionResponse(BaseModel):
    """Response model for skill extraction with dual ESCO/FGR mapping."""
    job_title: str = Field(description="Job title from the vacancy")
    extracted: List[ExtractedCompetency] = Field(
        description="Flattened list of extracted competencies with their matches"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "job_title": "Data Scientist",
                    "extracted": [
                        {
                            "raw_mention": "data analysis",
                            "class": "competency",
                            "uri": "http://data.europa.eu/esco/skill/a571ae14-3e16-4fd3-a615-5646e0b0b696",
                            "title": "gegevens inspecteren",
                            "description": "Analyseren, transformeren en modelleren van gegevens om nuttige informatie te ontdekken en om de besluitvorming te ondersteunen.",
                            "similarity_score": 0.8493559540085848,
                            "ontology": "esco"
                        },
                        {
                            "raw_mention": "data analysis",
                            "class": "competency",
                            "uri": "https://objectiveye.ai/fgr/competency/analyseren",
                            "title": "Analyseren",
                            "description": "Het vermogen om informatie te analyseren",
                            "similarity_score": 0.95,
                            "ontology": "fgr"
                        },
                        {
                            "raw_mention": "machine learning",
                            "class": "competency",
                            "uri": "http://data.europa.eu/esco/skill/machine-learning",
                            "title": "machine learning",
                            "description": "Toepassen van machine learning technieken",
                            "similarity_score": 0.98,
                            "ontology": "esco"
                        }
                    ]
                }
            ]
        }
    )

