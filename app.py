from experta import *
from flask import Flask, request, jsonify, render_template
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Fact definitions to hold user inputs and recommendations
class ProjectFact(Fact):
    """Fact for holding user input."""
    size = Field(str, mandatory=False)
    complexity = Field(str, mandatory=False)
    deadline = Field(str, mandatory=False)
    team_experience = Field(str, mandatory=False)
    risk = Field(str, mandatory=False)

class Recommendation(Fact):
    """Fact for holding recommendations."""
    approach = Field(str, mandatory=True)
    confidence = Field(float, mandatory=True)  # Confidence as float
    explanation = Field(str, mandatory=True)
    alternatives = Field(list, mandatory=False)

# Expert system for project management recommendations
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
            alternatives=[
                {"approach": "Scrum", "confidence": 0.9, "explanation": "Scrum works well as a lightweight Agile framework for iterative development."}
            ]
        ))

    @Rule(ProjectFact(size="large", complexity="high", deadline="strict", team_experience="low"))
    def recommend_waterfall(self):
        self.declare(Recommendation(
            approach="Waterfall",
            confidence=1.0,
            explanation="Waterfall is ideal for large, high-complexity projects with strict deadlines and less experienced teams.",
            alternatives=[
                {"approach": "Hybrid", "confidence": 0.85, "explanation": "Hybrid can mix the structured phases of Waterfall with Agile's flexibility."}
            ]
        ))

    @Rule(ProjectFact(size="medium", complexity="medium", deadline="flexible", team_experience="high"))
    def recommend_scrum(self):
        self.declare(Recommendation(
            approach="Scrum",
            confidence=1.0,
            explanation="Scrum is best for medium-sized projects with moderate complexity, flexible deadlines, and experienced teams.",
            alternatives=[
                {"approach": "Agile", "confidence": 0.9, "explanation": "Agile provides a more generalized iterative framework."}
            ]
        ))

    @Rule(ProjectFact(size="large", complexity="high", deadline="strict", team_experience="high", risk="high"))
    def recommend_risk_management(self):
        self.declare(Recommendation(
            approach="Risk Management Approach",
            confidence=0.9,
            explanation="Large, high-complexity projects with high risk and strict deadlines require a structured risk management approach.",
            alternatives=[
                {"approach": "Waterfall", "confidence": 0.8, "explanation": "Waterfall provides a highly structured approach for critical projects."},
                {"approach": "Hybrid", "confidence": 0.85, "explanation": "Hybrid balances structured phases with adaptive elements."}
            ]
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
    try:
        user_input = request.json
        logging.debug(f"User input received: {user_input}")

        # Check for missing or unknown inputs and track incomplete answers
        missing_fields = []
        for field in ["size", "complexity", "deadline", "team_experience", "risk"]:
            if not user_input.get(field):
                missing_fields.append(field)

        # If there are missing fields, ask for clarification
        if missing_fields:
            clarification_message = ask_for_missing_input(missing_fields)
            return jsonify({"message": clarification_message})

        # Reset the engine before processing new input
        engine.reset()

        # Declare facts based on user input
        engine.declare(ProjectFact(
            size=user_input.get("size"),
            complexity=user_input.get("complexity"),
            deadline=user_input.get("deadline"),
            team_experience=user_input.get("team_experience"),
            risk=user_input.get("risk")
        ))

        # Run the engine to evaluate rules
        engine.run()

        # Get the recommendations from the system
        recommendations = engine.get_recommendations()
        results = []

        # If recommendations exist, process them
        if recommendations:
            for rec in recommendations:
                # Convert confidence to percentage
                confidence_percentage = rec["confidence"] * 100

                # Properly format the alternatives
                alternatives = []
                for alt in rec.get("alternatives", []):
                    alt_confidence_percentage = alt["confidence"] * 100
                    alternatives.append({
                        "approach": alt["approach"],
                        "confidence": f"{alt_confidence_percentage:.2f}%",
                        "explanation": alt["explanation"]
                    })

                results.append({
                    "approach": rec["approach"],
                    "confidence": f"{confidence_percentage:.2f}%",
                    "explanation": rec["explanation"],
                    "alternatives": alternatives  # Structured alternatives
                })
        else:
            # If no recommendations, provide default feedback
            results.append({
                "approach": "None",
                "confidence": "0%",
                "explanation": "Insufficient data to provide a recommendation.",
                "alternatives": []
            })

        return jsonify(results)

    except Exception as e:
        logging.error(f"Error processing recommendation: {e}")
        return jsonify({"message": "Sorry, something went wrong. Please try again later."})

# Function to handle feedback and interactions in the system
def ask_for_missing_input(missing_fields):
    """Generate a clarification question based on missing fields."""
    return f"Explanation: The project {' and '.join(missing_fields)} are missing. Can you provide values for them?"

if __name__ == "__main__":
    app.run(debug=True)
