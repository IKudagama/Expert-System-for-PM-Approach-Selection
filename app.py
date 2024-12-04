from experta import *
from flask import Flask, request, jsonify, render_template

class ProjectFact(Fact):
    """Fact for holding user input."""
    size = Field(str, mandatory=False)
    complexity = Field(str, mandatory=False)
    deadline = Field(str, mandatory=False)
    team_experience = Field(str, mandatory=False)
    risk = Field(str, mandatory=False)  # New field to factor in risk level

class Recommendation(Fact):
    """Fact for holding recommendations."""
    approach = Field(str, mandatory=True)
    confidence = Field(float, mandatory=True)
    explanation = Field(str, mandatory=True)
    alternatives = Field(list, mandatory=False)

class ProjectManagementExpertSystem(KnowledgeEngine):
    @DefFacts()
    def initial_facts(self):
        yield Fact(started=True)

    @Rule(ProjectFact(size="small", complexity="low", deadline="flexible", team_experience="high"))
    def recommend_agile(self):
        self.declare(Recommendation(
            approach="Agile",
            confidence=1.0,
            explanation="Agile is ideal for small projects with low complexity, flexible deadlines, and experienced teams.",
            alternatives=["Scrum"]
        ))

    @Rule(ProjectFact(size="large", complexity="high", deadline="strict", team_experience="low"))
    def recommend_waterfall(self):
        self.declare(Recommendation(
            approach="Waterfall",
            confidence=1.0,
            explanation="Waterfall is ideal for large, high-complexity projects with strict deadlines and less experienced teams.",
            alternatives=["Hybrid"]
        ))

    @Rule(ProjectFact(size="medium", complexity="medium", deadline="flexible", team_experience="high"))
    def recommend_scrum(self):
        self.declare(Recommendation(
            approach="Scrum",
            confidence=1.0,
            explanation="Scrum is best for medium-sized projects with moderate complexity, flexible deadlines, and experienced teams.",
            alternatives=["Agile"]
        ))

    @Rule(OR(
        ProjectFact(size=MATCH.size, complexity="low", deadline="flexible"),
        ProjectFact(size=MATCH.size, complexity="medium", deadline="strict")
    ))
    def recommend_hybrid(self, size):
        self.declare(Recommendation(
            approach="Hybrid",
            confidence=0.8,
            explanation="Hybrid is suitable for projects with mixed requirements and flexible deadlines.",
            alternatives=["Waterfall"]
        ))

    # New rules based on risk and size
    @Rule(ProjectFact(size="large", complexity="high", deadline="strict", team_experience="high", risk="high"))
    def recommend_risk_management(self):
        self.declare(Recommendation(
            approach="Risk Management Approach",
            confidence=0.9,
            explanation="Large, high-complexity projects with high risk and strict deadlines require a structured risk management approach.",
            alternatives=["Waterfall", "Hybrid"]
        ))

    @Rule(ProjectFact(size="small", complexity="low", deadline="strict", team_experience="low", risk="low"))
    def recommend_simple_agile(self):
        self.declare(Recommendation(
            approach="Simple Agile",
            confidence=0.85,
            explanation="Small, low-complexity projects with strict deadlines and minimal risk benefit from simple Agile approaches.",
            alternatives=["Kanban"]
        ))

    @Rule(ProjectFact(size="large", complexity="medium", deadline="flexible", team_experience="medium", risk="medium"))
    def recommend_scaled_scrum(self):
        self.declare(Recommendation(
            approach="Scaled Scrum",
            confidence=0.75,
            explanation="Large projects with medium complexity and flexible deadlines are suited for scaled Scrum implementations.",
            alternatives=["Scrum"]
        ))

    @Rule(ProjectFact(size="medium", complexity="high", deadline="strict", team_experience="low", risk="high"))
    def recommend_waterfall_with_risk_plan(self):
        self.declare(Recommendation(
            approach="Waterfall with Risk Plan",
            confidence=0.9,
            explanation="For high-risk, high-complexity projects with strict deadlines and less experienced teams, a risk-managed Waterfall approach is ideal.",
            alternatives=["Hybrid"]
        ))

    # New rule for projects with low complexity and no deadlines
    @Rule(ProjectFact(size="small", complexity="low", deadline="no deadline", team_experience="high"))
    def recommend_lean(self):
        self.declare(Recommendation(
            approach="Lean",
            confidence=0.85,
            explanation="For small projects with low complexity and no strict deadlines, a Lean approach is effective.",
            alternatives=["Kanban"]
        ))

    @Rule(AND(
        NOT(ProjectFact(size=W())), 
        NOT(ProjectFact(complexity=W())), 
        NOT(ProjectFact(deadline=W())), 
        NOT(ProjectFact(team_experience=W()))
    ))
    def no_input(self):
        self.declare(Recommendation(
            approach="None",
            confidence=0.0,
            explanation="Insufficient data to provide a recommendation.",
            alternatives=[]
        ))

    def get_recommendations(self):
        return [fact for fact in self.facts.values() if isinstance(fact, Recommendation)]

# Initialize Flask app
app = Flask(__name__)

# Initialize the expert system
engine = ProjectManagementExpertSystem()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get_recommendation", methods=["POST"])
def get_recommendation():
    user_input = request.json

    # Reset and declare facts in the expert system
    engine.reset()
    engine.declare(ProjectFact(
        size=user_input.get("size"),
        complexity=user_input.get("complexity"),
        deadline=user_input.get("deadline"),
        team_experience=user_input.get("team_experience"),
        risk=user_input.get("risk")  # Added new field for risk
    ))
    
    # Run the engine
    engine.run()

    # Fetch recommendations
    recommendations = engine.get_recommendations()
    results = []
    for rec in recommendations:
        results.append({
            "approach": rec["approach"],
            "confidence": rec["confidence"],
            "explanation": rec["explanation"],
            "alternatives": rec.get("alternatives", [])
        })

    # If no recommendations, provide feedback
    if not results:
        results.append({
            "approach": "None",
            "confidence": 0.0,
            "explanation": "Insufficient data to provide a recommendation.",
            "alternatives": []
        })

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
