"""
Practice routes - Voice Practice with Shadow Reading Strategy
"""
import os
import random
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db, models

router = APIRouter()

# Extended passages for Shadow Reading with multiple difficulty levels
SHADOW_PASSAGES = {
    "es": {
        "greetings": [
            {"sentence": "¡Hola! ¿Cómo estás hoy?", "translation": "Hello! How are you today?", "description": "Casual greeting", "difficulty": "beginner"},
            {"sentence": "Buenos días, ¿cómo amaneciste?", "translation": "Good morning, how did you wake up?", "description": "Morning greeting", "difficulty": "beginner"},
            {"sentence": "Mucho gusto en conocerte.", "translation": "Nice to meet you.", "description": "Formal introduction", "difficulty": "beginner"},
            {"sentence": "¿Qué tal tu día?", "translation": "How's your day going?", "description": "Casual check-in", "difficulty": "intermediate"},
            {"sentence": "Me alegra verte de nuevo.", "translation": "I'm glad to see you again.", "description": "Reunion greeting", "difficulty": "intermediate"},
            {"sentence": "¿Cómo está usted? Hace mucho tiempo.", "translation": "How are you? It's been a long time.", "description": "Formal reunion", "difficulty": "advanced"},
            {"sentence": "¡Qué sorpresa verte por aquí!", "translation": "What a surprise to see you here!", "description": "Surprise greeting", "difficulty": "advanced"}
        ],
        "restaurant": [
            {"sentence": "Me gustaría una mesa para dos, por favor.", "translation": "I would like a table for two.", "description": "Requesting a table", "difficulty": "beginner"},
            {"sentence": "¿Tiene reservación?", "translation": "Do you have a reservation?", "description": "Asking about reservation", "difficulty": "beginner"},
            {"sentence": "Quisiera ver el menú, por favor.", "translation": "I would like to see the menu.", "description": "Asking for menu", "difficulty": "beginner"},
            {"sentence": "¿Qué me recomienda el chef?", "translation": "What does the chef recommend?", "description": "Asking for recommendation", "difficulty": "intermediate"},
            {"sentence": "La cuenta, por favor. ¿Aceptan tarjeta?", "translation": "The check, please. Do you accept card?", "description": "Requesting the bill", "difficulty": "intermediate"},
            {"sentence": "Para mí será el pescado, sin salsa.", "translation": "I'll have the fish, without sauce.", "description": "Ordering food", "difficulty": "advanced"},
            {"sentence": "¿Podría traernos más agua, por favor?", "translation": "Could you bring us more water?", "description": "Getting server attention", "difficulty": "advanced"}
        ],
        "shopping": [
            {"sentence": "¿Cuánto cuesta esto?", "translation": "How much does this cost?", "description": "Asking price", "difficulty": "beginner"},
            {"sentence": "¿Tiene esto en otro color?", "translation": "Do you have this in another color?", "description": "Asking about colors", "difficulty": "beginner"},
            {"sentence": "¿Puedo probarme esto?", "translation": "Can I try this on?", "description": "Asking to try on", "difficulty": "beginner"},
            {"sentence": "Estoy buscando un regalo para mi amigo.", "translation": "I'm looking for a gift for my friend.", "description": "Shopping for a gift", "difficulty": "intermediate"},
            {"sentence": "¿Hace descuento por pago en efectivo?", "translation": "Do you give a discount for cash?", "description": "Asking for discount", "difficulty": "intermediate"},
            {"sentence": "¿Tienen una política de devolución?", "translation": "Do you have a return policy?", "description": "Asking about returns", "difficulty": "advanced"},
            {"sentence": "Esto me queda un poco ajustado. ¿Tiene una talla más grande?", "translation": "This fits a bit tight. Do you have a larger size?", "description": "Clothing exchange", "difficulty": "advanced"}
        ],
        "directions": [
            {"sentence": "¿Dónde está la estación de tren?", "translation": "Where is the train station?", "description": "Asking for station", "difficulty": "beginner"},
            {"sentence": "¿Está lejos el centro?", "translation": "Is the downtown far?", "description": "Asking about distance", "difficulty": "beginner"},
            {"sentence": "¿Cómo llego al museo desde aquí?", "translation": "How do I get to the museum from here?", "description": "Asking for directions", "difficulty": "intermediate"},
            {"sentence": "Gire a la izquierda en el semáforo.", "translation": "Turn left at the traffic light.", "description": "Giving directions", "difficulty": "intermediate"},
            {"sentence": "Camine dos cuadras straight y lo verá a la derecha.", "translation": "Walk two blocks straight and you'll see it on the right.", "description": "Detailed directions", "difficulty": "advanced"},
            {"sentence": "¿Hay un baño público cerca de aquí?", "translation": "Is there a public restroom near here?", "description": "Asking for facilities", "difficulty": "advanced"},
            {"sentence": "Perdón, ¿me podría indicar cómo llegar al banco?", "translation": "Excuse me, could you tell me how to get to the bank?", "description": "Polite direction asking", "difficulty": "advanced"}
        ],
        "travel": [
            {"sentence": "Necesito un taxi al aeropuerto, por favor.", "translation": "I need a taxi to the airport.", "description": "Booking a taxi", "difficulty": "beginner"},
            {"sentence": "¿A qué hora sale el vuelo a Madrid?", "translation": "What time does the flight to Madrid depart?", "description": "Asking about flight", "difficulty": "intermediate"},
            {"sentence": "Tengo una conexión en Frankfurt.", "translation": "I have a connection in Frankfurt.", "description": "Flight connection", "difficulty": "intermediate"},
            {"sentence": "¿Dónde puedo alquilar un coche?", "translation": "Where can I rent a car?", "description": "Renting a car", "difficulty": "intermediate"},
            {"sentence": "El vuelo se ha retrasado dos horas.", "translation": "The flight has been delayed by two hours.", "description": "Flight delay", "difficulty": "advanced"},
            {"sentence": "Mi maleta no llegó con mi vuelo.", "translation": "My suitcase didn't arrive with my flight.", "description": "Lost luggage", "difficulty": "advanced"},
            {"sentence": "¿Cuánto tiempo dura el viaje en tren a Barcelona?", "translation": "How long does the train trip to Barcelona take?", "description": "Travel time inquiry", "difficulty": "advanced"}
        ],
        "daily": [
            {"sentence": "Es hora de levantarse.", "translation": "It's time to get up.", "description": "Morning routine", "difficulty": "beginner"},
            {"sentence": "No tengo apetito esta mañana.", "translation": "I don't have appetite this morning.", "description": "Breakfast conversation", "difficulty": "intermediate"},
            {"sentence": "Tengo que trabajar hasta las seis.", "translation": "I have to work until six.", "description": "Talking about schedule", "difficulty": "intermediate"},
            {"sentence": "¿Qué quieres hacer este fin de semana?", "translation": "What do you want to do this weekend?", "description": "Weekend plans", "difficulty": "intermediate"},
            {"sentence": "Ya es demasiado tarde para cambiar de opinión.", "translation": "It's already too late to change your mind.", "description": "Expressing frustration", "difficulty": "advanced"},
            {"sentence": "No me importa lo que digan los demás.", "translation": "I don't care what others say.", "description": "Expressing opinion", "difficulty": "advanced"},
            {"sentence": "Deberíamos planificar esto con más anticipación.", "translation": "We should plan this with more advance.", "description": "Planning discussion", "difficulty": "advanced"}
        ]
    },
    "en": {
        "greetings": [
            {"sentence": "Hello! How are you today?", "translation": "你好！你今天怎么样？", "description": "Casual greeting", "difficulty": "beginner"},
            {"sentence": "Good morning! Did you sleep well?", "translation": "早上好！你睡得好吗？", "description": "Morning greeting", "difficulty": "beginner"},
            {"sentence": "Nice to meet you. I'm John.", "translation": "很高兴认识你。我是约翰。", "description": "Formal introduction", "difficulty": "beginner"},
            {"sentence": "Long time no see! How have you been?", "translation": "好久不见！你最近怎么样？", "description": "Reunion greeting", "difficulty": "intermediate"},
            {"sentence": "What a pleasant surprise running into you!", "translation": "真惊喜能遇到你！", "description": "Surprise greeting", "difficulty": "advanced"},
            {"sentence": "It's great to see you again after all these years.", "translation": "这么多年后再次见到你真高兴。", "description": "Emotional reunion", "difficulty": "advanced"},
            {"sentence": "How have you been holding up lately?", "translation": "你最近过得怎么样？", "description": "Caring check-in", "difficulty": "advanced"}
        ],
        "restaurant": [
            {"sentence": "I would like a table for two, please.", "translation": "我想要一张两人桌，谢谢。", "description": "Requesting a table", "difficulty": "beginner"},
            {"sentence": "Do you have any reservations?", "translation": "您有预订吗？", "description": "Asking about reservation", "difficulty": "beginner"},
            {"sentence": "Could I see the menu, please?", "translation": "请问可以看一下菜单吗？", "description": "Asking for menu", "difficulty": "beginner"},
            {"sentence": "What's the chef's special today?", "translation": "今天厨师有什么特别推荐吗？", "description": "Asking for recommendation", "difficulty": "intermediate"},
            {"sentence": "We would like to order dessert now.", "translation": "我们现在想点甜点。", "description": "Ordering dessert", "difficulty": "intermediate"},
            {"sentence": "I would like the steak, medium rare, with a side of vegetables.", "translation": "我想要牛排，五分熟，外加一份蔬菜。", "description": "Detailed order", "difficulty": "advanced"},
            {"sentence": "Could we have the check, please? We're in a bit of a hurry.", "translation": "请给我们结账。我们有点赶时间。", "description": "Rushing checkout", "difficulty": "advanced"}
        ],
        "shopping": [
            {"sentence": "How much does this cost?", "translation": "这个多少钱？", "description": "Asking price", "difficulty": "beginner"},
            {"sentence": "Do you have this in a smaller size?", "translation": "有小一点的尺码吗？", "description": "Asking about sizes", "difficulty": "beginner"},
            {"sentence": "Can I try this on?", "translation": "我可以试穿吗？", "description": "Asking to try on", "difficulty": "beginner"},
            {"sentence": "I'm looking for a birthday gift for my sister.", "translation": "我在给我妹妹找生日礼物。", "description": "Shopping for a gift", "difficulty": "intermediate"},
            {"sentence": "Is there any discount if I pay in cash?", "translation": "现金付款有折扣吗？", "description": "Asking for discount", "difficulty": "intermediate"},
            {"sentence": "Do you have a warranty or return policy for this product?", "translation": "这个产品有保修或退货政策吗？", "description": "Warranty inquiry", "difficulty": "advanced"},
            {"sentence": "I'm sorry, but this doesn't fit me well. Could I exchange it for a different size?", "translation": "抱歉，这件不太合身。我可以换其他尺码吗？", "description": "Exchange request", "difficulty": "advanced"}
        ],
        "directions": [
            {"sentence": "Where is the train station?", "translation": "火车站在哪里？", "description": "Asking for station", "difficulty": "beginner"},
            {"sentence": "Is the city center far from here?", "translation": "市中心离这里远吗？", "description": "Asking about distance", "difficulty": "beginner"},
            {"sentence": "How do I get to the museum from here?", "translation": "从这里去博物馆怎么走？", "description": "Asking for directions", "difficulty": "intermediate"},
            {"sentence": "Turn left at the traffic light.", "translation": "在红绿灯左转。", "description": "Giving directions", "difficulty": "intermediate"},
            {"sentence": "Go straight for two blocks and you'll see it on your right.", "translation": "直走两个街区，你会看到它在你的右边。", "description": "Detailed directions", "difficulty": "advanced"},
            {"sentence": "Is there a public restroom within walking distance?", "translation": "步行范围内有公共厕所吗？", "description": "Asking for facilities", "difficulty": "advanced"},
            {"sentence": "Excuse me, could you point me in the direction of the nearest bank?", "translation": "打扰一下，你能告诉我最近的银行在哪里吗？", "description": "Polite direction asking", "difficulty": "advanced"}
        ],
        "travel": [
            {"sentence": "I need a taxi to the airport, please.", "translation": "我需要一辆去机场的出租车。", "description": "Booking a taxi", "difficulty": "beginner"},
            {"sentence": "What time does the flight to Paris depart?", "translation": "去巴黎的航班几点起飞？", "description": "Asking about flight", "difficulty": "intermediate"},
            {"sentence": "I have a layover in London.", "translation": "我在伦敦转机。", "description": "Flight connection", "difficulty": "intermediate"},
            {"sentence": "Where can I rent a car?", "translation": "我在哪里可以租车？", "description": "Renting a car", "difficulty": "intermediate"},
            {"sentence": "The flight has been delayed due to bad weather.", "translation": "由于天气恶劣，航班延误了。", "description": "Flight delay", "difficulty": "advanced"},
            {"sentence": "My luggage didn't arrive with my flight. I need to file a claim.", "translation": "我的行李没有随航班到达。我需要提交索赔。", "description": "Lost luggage", "difficulty": "advanced"},
            {"sentence": "How long does it take to get to the city center by train?", "translation": "乘火车去市中心需要多长时间？", "description": "Travel time inquiry", "difficulty": "advanced"}
        ],
        "daily": [
            {"sentence": "It's time to wake up.", "translation": "该起床了。", "description": "Morning routine", "difficulty": "beginner"},
            {"sentence": "I don't feel like eating anything this morning.", "translation": "今天早上我不想吃任何东西。", "description": "Breakfast conversation", "difficulty": "intermediate"},
            {"sentence": "I have to work overtime today.", "translation": "我今天要加班。", "description": "Talking about schedule", "difficulty": "intermediate"},
            {"sentence": "What are you planning to do this weekend?", "translation": "你计划这个周末做什么？", "description": "Weekend plans", "difficulty": "intermediate"},
            {"sentence": "It's already too late to turn back now.", "translation": "现在回头已经太晚了。", "description": "Expressing frustration", "difficulty": "advanced"},
            {"sentence": "I really couldn't care less about what people think of me.", "translation": "我真的不在乎别人怎么看我。", "description": "Expressing opinion", "difficulty": "advanced"},
            {"sentence": "We should have planned this much earlier in advance.", "translation": "我们应该更早计划这件事。", "description": "Planning discussion", "difficulty": "advanced"}
        ]
    },
    "fr": {
        "greetings": [
            {"sentence": "Bonjour! Comment allez-vous aujourd'hui?", "translation": "你好！你今天怎么样？", "description": "Formal greeting", "difficulty": "beginner"},
            {"sentence": "Bonsoir, ça va bien?", "translation": "晚上好，你好吗？", "description": "Evening greeting", "difficulty": "beginner"},
            {"sentence": "Enchanté de faire votre connaissance.", "translation": "很高兴认识您。", "description": "Formal introduction", "difficulty": "beginner"},
            {"sentence": "Ça fait longtemps! Tu vas bien?", "translation": "好久不见！你好吗？", "description": "Casual reunion", "difficulty": "intermediate"},
            {"sentence": "Quel plaisir de te revoir!", "translation": "很高兴再次见到你！", "description": "Warm reunion", "difficulty": "intermediate"},
            {"sentence": "Ça fait des années! Tu as changé!", "translation": "好多年了！你变了！", "description": "Long-time reunion", "difficulty": "advanced"},
            {"sentence": "Je suis ravi de faire votre connaissance finalmente.", "translation": "终于很高兴认识您。", "description": "Formal elaborate greeting", "difficulty": "advanced"}
        ],
        "restaurant": [
            {"sentence": "Je voudrais une table pour deux, s'il vous plaît.", "translation": "我想要一张两人桌，谢谢。", "description": "Requesting a table", "difficulty": "beginner"},
            {"sentence": "Avez-vous une réservation?", "translation": "您有预订吗？", "description": "Asking about reservation", "difficulty": "beginner"},
            {"sentence": "La carte, s'il vous plaît.", "translation": "请给我菜单。", "description": "Asking for menu", "difficulty": "beginner"},
            {"sentence": "Qu'est-ce que vous recommandez?", "translation": "您推荐什么？", "description": "Asking for recommendation", "difficulty": "intermediate"},
            {"sentence": "L'addition, s'il vous plaît. Acceptez-vous les cartes?", "translation": "请结账。你们接受卡吗？", "description": "Requesting the bill", "difficulty": "intermediate"},
            {"sentence": "Je prendrai le saumon, sans sauce, avec des légumes.", "translation": "我要三文鱼，不要酱，配蔬菜。", "description": "Detailed order", "difficulty": "advanced"},
            {"sentence": "Pourriez-vous nous apporter plus d'eau, s'il vous plaît?", "translation": "请您给我们多拿点水好吗？", "description": "Getting server attention", "difficulty": "advanced"}
        ],
        "shopping": [
            {"sentence": "Combien ça coûte?", "translation": "这个多少钱？", "description": "Asking price", "difficulty": "beginner"},
            {"sentence": "Avez-vous ceci dans une autre couleur?", "translation": "这个有其他颜色吗？", "description": "Asking about colors", "difficulty": "beginner"},
            {"sentence": "Puis-je essayer ceci?", "translation": "我可以试穿这个吗？", "description": "Asking to try on", "difficulty": "beginner"},
            {"sentence": "Je cherche un cadeau pour mon ami.", "translation": "我在给我朋友找礼物。", "description": "Shopping for a gift", "difficulty": "intermediate"},
            {"sentence": "Faites-vous un descuento pour paiement comptant?", "translation": "现金付款有折扣吗？", "description": "Asking for discount", "difficulty": "intermediate"},
            {"sentence": "Avez-vous une politique de retour pour cet article?", "translation": "这件商品有退货政策吗？", "description": "Return policy inquiry", "difficulty": "advanced"},
            {"sentence": "Ce modèle me semble un peu serré. Avez-vous une taille plus grande?", "translation": "这款我穿着有点紧。有大一点的尺码吗？", "description": "Size exchange", "difficulty": "advanced"}
        ],
        "directions": [
            {"sentence": "Où est la gare?", "translation": "火车站在哪里？", "description": "Asking for station", "difficulty": "beginner"},
            {"sentence": "Le centre-ville est-il loin d'ici?", "translation": "市中心离这里远吗？", "description": "Asking about distance", "difficulty": "beginner"},
            {"sentence": "Comment aller au musée d'ici?", "translation": "从这里去博物馆怎么走？", "description": "Asking for directions", "difficulty": "intermediate"},
            {"sentence": "Tournez à gauche au feu.", "translation": "在红绿灯左转。", "description": "Giving directions", "difficulty": "intermediate"},
            {"sentence": "Continuez tout droit pendant deux blocs, vous le verrez à droite.", "translation": "直走两个街区，你会看到它在右边。", "description": "Detailed directions", "difficulty": "advanced"},
            {"sentence": "Y a-t-il des toilettes publiques à proximité?", "translation": "附近有公共厕所吗？", "description": "Asking for facilities", "difficulty": "advanced"},
            {"sentence": "Excusez-moi, pourriez-vous m'indiquer où se trouve la banque?", "translation": "打扰一下，您能告诉我银行在哪里吗？", "description": "Polite direction asking", "difficulty": "advanced"}
        ],
        "travel": [
            {"sentence": "J'ai besoin d'un taxi pour l'aéroport, s'il vous plaît.", "translation": "我需要一辆去机场的出租车。", "description": "Booking a taxi", "difficulty": "beginner"},
            {"sentence": "À quelle heure part le vol pour Paris?", "translation": "去巴黎的航班几点起飞？", "description": "Asking about flight", "difficulty": "intermediate"},
            {"sentence": "J'ai une correspondance à Londres.", "translation": "我在伦敦转机。", "description": "Flight connection", "difficulty": "intermediate"},
            {"sentence": "Où puis-je louer une voiture?", "translation": "我在哪里可以租车？", "description": "Renting a car", "difficulty": "intermediate"},
            {"sentence": "Le vol a été retardé à cause du mauvais temps.", "translation": "由于天气恶劣，航班延误了。", "description": "Flight delay", "difficulty": "advanced"},
            {"sentence": "Ma valise n'est pas arrivée avec mon vol. Je dois déposer une réclamation.", "translation": "我的行李没有随航班到达。我需要提交索赔。", "description": "Lost luggage", "difficulty": "advanced"},
            {"sentence": "Combien de temps faut-il pour aller au centre-ville en train?", "translation": "乘火车去市中心需要多长时间？", "description": "Travel time inquiry", "difficulty": "advanced"}
        ],
        "daily": [
            {"sentence": "Il est temps de se lever.", "translation": "该起床了。", "description": "Morning routine", "difficulty": "beginner"},
            {"sentence": "Je n'ai pas faim ce matin.", "translation": "今天早上我不饿。", "description": "Breakfast conversation", "difficulty": "intermediate"},
            {"sentence": "Je dois travailler jusqu'à six heures.", "translation": "我要工作到六点。", "description": "Talking about schedule", "difficulty": "intermediate"},
            {"sentence": "Qu'est-ce que tu vas faire ce week-end?", "translation": "你这个周末要做什么？", "description": "Weekend plans", "difficulty": "intermediate"},
            {"sentence": "Il est déjà trop tard pour changer d'avis.", "translation": "现在改变主意已经太晚了。", "description": "Expressing frustration", "difficulty": "advanced"},
            {"sentence": "Je m'en fiche royalement de ce que les autres pensent.", "translation": "我完全不在乎别人怎么想。", "description": "Expressing opinion", "difficulty": "advanced"},
            {"sentence": "Nous aurions dû planifier cela bien plus à l'avance.", "translation": "我们应该更早计划这件事。", "description": "Planning discussion", "difficulty": "advanced"}
        ]
    },
    "de": {
        "greetings": [
            {"sentence": "Hallo! Wie geht es dir heute?", "translation": "你好！你今天怎么样？", "description": "Casual greeting", "difficulty": "beginner"},
            {"sentence": "Guten Morgen! Hast du gut geschlafen?", "translation": "早上好！睡得好吗？", "description": "Morning greeting", "difficulty": "beginner"},
            {"sentence": "Freut mich, dich kennenzulernen.", "translation": "很高兴认识你。", "description": "Introduction", "difficulty": "beginner"},
            {"sentence": "Lange nicht gesehen! Wie geht's dir?", "translation": "好久不见！你好吗？", "description": "Reunion greeting", "difficulty": "intermediate"},
            {"sentence": "Was für eine Überraschung, dich hier zu sehen!", "translation": "真惊喜能在这里见到你！", "description": "Surprise greeting", "difficulty": "advanced"},
            {"sentence": "Es ist schön, dich nach so langer Zeit wiederzusehen.", "translation": "这么久后再次见到你真高兴。", "description": "Emotional reunion", "difficulty": "advanced"},
            {"sentence": "Wie hast du die ganze Zeit überlebt?", "translation": "这段时间你是怎么过来的？", "description": "Caring check-in", "difficulty": "advanced"}
        ],
        "restaurant": [
            {"sentence": "Ich möchte einen Tisch für zwei, bitte.", "translation": "我想要一张两人桌，谢谢。", "description": "Requesting a table", "difficulty": "beginner"},
            {"sentence": "Haben Sie eine Reservierung?", "translation": "您有预订吗？", "description": "Asking about reservation", "difficulty": "beginner"},
            {"sentence": "Könnte ich die Speisekarte sehen?", "translation": "可以看一下菜单吗？", "description": "Asking for menu", "difficulty": "beginner"},
            {"sentence": "Was empfiehlt der Koch heute?", "translation": "厨师今天推荐什么？", "description": "Asking for recommendation", "difficulty": "intermediate"},
            {"sentence": "Die Rechnung, bitte. Akzeptieren Sie Karten?", "translation": "请结账。你们接受卡吗？", "description": "Requesting the bill", "difficulty": "intermediate"},
            {"sentence": "Ich hätte gern das Steak, medium, mit Gemüse als Beilage.", "translation": "我想要牛排，五分熟，配蔬菜。", "description": "Detailed order", "difficulty": "advanced"},
            {"sentence": "Könnten wir bitte noch etwas Wasser bekommen?", "translation": "请给我们再拿点水好吗？", "description": "Getting server attention", "difficulty": "advanced"}
        ],
        "shopping": [
            {"sentence": "Wie viel kostet das?", "translation": "这个多少钱？", "description": "Asking price", "difficulty": "beginner"},
            {"sentence": "Haben Sie das in einer anderen Farbe?", "translation": "这个有其他颜色吗？", "description": "Asking about colors", "difficulty": "beginner"},
            {"sentence": "Kann ich das anprobieren?", "translation": "我可以试穿吗？", "description": "Asking to try on", "difficulty": "beginner"},
            {"sentence": "Ich suche ein Geschenk für meinen Freund.", "translation": "我在给我朋友找礼物。", "description": "Shopping for a gift", "difficulty": "intermediate"},
            {"sentence": "Gibt es einen Rabatt bei Barzahlung?", "translation": "现金付款有折扣吗？", "description": "Asking for discount", "difficulty": "intermediate"},
            {"sentence": "Haben Sie eine Garantie oder Rückgaberecht für dieses Produkt?", "translation": "这个产品有保修或退货权吗？", "description": "Warranty inquiry", "difficulty": "advanced"},
            {"sentence": "Das passt mir nicht gut. Kann ich es gegen eine andere Größe umtauschen?", "translation": "这不太合身。我可以换其他尺码吗？", "description": "Exchange request", "difficulty": "advanced"}
        ],
        "directions": [
            {"sentence": "Wo ist der Bahnhof?", "translation": "火车站在哪里？", "description": "Asking for station", "difficulty": "beginner"},
            {"sentence": "Ist das Stadtzentrum weit von hier?", "translation": "市中心离这里远吗？", "description": "Asking about distance", "difficulty": "beginner"},
            {"sentence": "Wie komme ich von hier zum Museum?", "translation": "从这里去博物馆怎么走？", "description": "Asking for directions", "difficulty": "intermediate"},
            {"sentence": "Biegen Sie links an der Ampel ab.", "translation": "在红绿灯左转。", "description": "Giving directions", "difficulty": "intermediate"},
            {"sentence": "Gehen Sie zwei Blocks geradeaus, dann sehen Sie es rechts.", "translation": "直走两个街区，你会看到它在右边。", "description": "Detailed directions", "difficulty": "advanced"},
            {"sentence": "Gibt es eine öffentliche Toilette in der Nähe?", "translation": "附近有公共厕所吗？", "description": "Asking for facilities", "difficulty": "advanced"},
            {"sentence": "Entschuldigung, könnten Sie mir den Weg zur nächsten Bank zeigen?", "translation": "打扰一下，您能告诉我最近的银行怎么走吗？", "description": "Polite direction asking", "difficulty": "advanced"}
        ],
        "travel": [
            {"sentence": "Ich brauche ein Taxi zum Flughafen, bitte.", "translation": "我需要一辆去机场的出租车。", "description": "Booking a taxi", "difficulty": "beginner"},
            {"sentence": "Wann fliegt das Flugzeug nach Berlin?", "translation": "去柏林的航班什么时候起飞？", "description": "Asking about flight", "difficulty": "intermediate"},
            {"sentence": "Ich habe einen Anschlussflug in Frankfurt.", "translation": "我在法兰克福转机。", "description": "Flight connection", "difficulty": "intermediate"},
            {"sentence": "Wo kann ich ein Auto mieten?", "translation": "我在哪里可以租车？", "description": "Renting a car", "difficulty": "intermediate"},
            {"sentence": "Der Flug wurde wegen schlechten Wetters verspätet.", "translation": "由于天气恶劣，航班延误了。", "description": "Flight delay", "difficulty": "advanced"},
            {"sentence": "Mein Koffer ist nicht mit meinem Flug angekommen. Ich muss einen Anspruch einreichen.", "translation": "我的行李没有随航班到达。我需要提交索赔。", "description": "Lost luggage", "difficulty": "advanced"},
            {"sentence": "Wie lange dauert die Fahrt mit dem Zug ins Stadtzentrum?", "translation": "乘火车去市中心需要多长时间？", "description": "Travel time inquiry", "difficulty": "advanced"}
        ],
        "daily": [
            {"sentence": "Es ist Zeit aufzustehen.", "translation": "该起床了。", "description": "Morning routine", "difficulty": "beginner"},
            {"sentence": "Ich habe heute Morgen keinen Appetit.", "translation": "今天早上我没有胃口。", "description": "Breakfast conversation", "difficulty": "intermediate"},
            {"sentence": "Ich muss bis sechs Uhr arbeiten.", "translation": "我要工作到六点。", "description": "Talking about schedule", "difficulty": "intermediate"},
            {"sentence": "Was hast du dieses Wochenende vor?", "translation": "你这个周末计划做什么？", "description": "Weekend plans", "difficulty": "intermediate"},
            {"sentence": "Es ist already zu spät, um es sich anders zu überlegen.", "translation": "现在改变主意已经太晚了。", "description": "Expressing frustration", "difficulty": "advanced"},
            {"sentence": "Es ist mir egal, was die anderen denken.", "translation": "我不在乎别人怎么想。", "description": "Expressing opinion", "difficulty": "advanced"},
            {"sentence": "Wir hätten das viel früher planen sollen.", "translation": "我们应该更早计划这件事。", "description": "Planning discussion", "difficulty": "advanced"}
        ]
    },
    "ja": {
        "greetings": [
            {"sentence": "こんにちは、お元気ですか？", "translation": "Hello, how are you?", "description": "Casual greeting", "difficulty": "beginner"},
            {"sentence": "おはようございます。よく眠れましたか？", "translation": "Good morning. Did you sleep well?", "description": "Morning greeting", "difficulty": "beginner"},
            {"sentence": "はじめまして、田中です。よろしくお願いします。", "translation": "Nice to meet you, I'm Tanaka. Please treat me well.", "description": "Formal introduction", "difficulty": "beginner"},
            {"sentence": "お久しぶりです。お元気でしたか？", "translation": "Long time no see. Have you been well?", "description": "Reunion greeting", "difficulty": "intermediate"},
            {"sentence": "ここで会えるなんて嬉しいです。", "translation": "I'm happy to meet you here.", "description": "Surprise greeting", "difficulty": "intermediate"},
            {"sentence": "ご無沙汰しております。お変わりございませんか？", "translation": "It's been a while. I hope you've been well?", "description": "Formal reunion", "difficulty": "advanced"},
            {"sentence": "お会いできて光栄です。先生からよくお話を伺っています。", "translation": "It's an honor to meet you. I've heard a lot about you from my teacher.", "description": "Very formal greeting", "difficulty": "advanced"}
        ],
        "restaurant": [
            {"sentence": "二人のテーブルをお願いします。", "translation": "A table for two, please.", "description": "Requesting a table", "difficulty": "beginner"},
            {"sentence": "予約している田中です。", "translation": "I'm Tanaka, I have a reservation.", "description": "Checking reservation", "difficulty": "beginner"},
            {"sentence": "メニューを見せてください。", "translation": "Please show me the menu.", "description": "Asking for menu", "difficulty": "beginner"},
            {"sentence": "おすすめは何ですか？", "translation": "What do you recommend?", "description": "Asking for recommendation", "difficulty": "intermediate"},
            {"sentence": "お会計お願いします。カードは使えますか？", "translation": "Check please. Can I use a card?", "description": "Requesting the bill", "difficulty": "intermediate"},
            {"sentence": "すみません、アレルギーがあるのですが、この料理に卵は入っていますか？", "translation": "Excuse me, I have allergies. Does this dish contain eggs?", "description": "Allergy inquiry", "difficulty": "advanced"},
            {"sentence": "予約していたのですが、30分遅れてしまいすみません。まだ大丈夫でしょうか？", "translation": "I had a reservation but I'm 30 minutes late. Is it still okay?", "description": "Late arrival apology", "difficulty": "advanced"}
        ],
        "shopping": [
            {"sentence": "これはいくらですか？", "translation": "How much is this?", "description": "Asking price", "difficulty": "beginner"},
            {"sentence": "他の色はありますか？", "translation": "Do you have other colors?", "description": "Asking about colors", "difficulty": "beginner"},
            {"sentence": "試着してもいいですか？", "translation": "May I try it on?", "description": "Asking to try on", "difficulty": "beginner"},
            {"sentence": "友達へのプレゼントを探しています。", "translation": "I'm looking for a gift for my friend.", "description": "Shopping for a gift", "difficulty": "intermediate"},
            {"sentence": "現金で払ったら割引はありますか？", "translation": "Is there a discount for cash payment?", "description": "Asking for discount", "difficulty": "intermediate"},
            {"sentence": "返品ポリシーはありますか？レシートは必要ですか？", "translation": "Do you have a return policy? Do I need a receipt?", "description": "Return policy inquiry", "difficulty": "advanced"},
            {"sentence": "すみません、サイズが合わないので、一つ大きいサイズに交換していただけますか？", "translation": "Excuse me, the size doesn't fit. Could you exchange for one size larger?", "description": "Size exchange", "difficulty": "advanced"}
        ],
        "directions": [
            {"sentence": "駅はどこですか？", "translation": "Where is the station?", "description": "Asking for station", "difficulty": "beginner"},
            {"sentence": "ここから遠いですか？", "translation": "Is it far from here?", "description": "Asking about distance", "difficulty": "beginner"},
            {"sentence": "美術館へはどうやって行けばいいですか？", "translation": "How do I get to the museum?", "description": "Asking for directions", "difficulty": "intermediate"},
            {"sentence": "信号を左に曲がってください。", "translation": "Please turn left at the traffic light.", "description": "Giving directions", "difficulty": "intermediate"},
            {"sentence": "この道をまっすぐ二ブロック行って、右側に見えます。", "translation": "Go straight on this road for two blocks, and you'll see it on the right.", "description": "Detailed directions", "difficulty": "advanced"},
            {"sentence": "すみません、近くにトイレはありますか？", "translation": "Excuse me, is there a restroom nearby?", "description": "Asking for facilities", "difficulty": "advanced"},
            {"sentence": "すみません、道に迷ってしまいました。この辺に銀行はありますか？", "translation": "Excuse me, I'm lost. Is there a bank around here?", "description": "Lost and asking", "difficulty": "advanced"}
        ],
        "travel": [
            {"sentence": "空港までタクシーをお願いします。", "translation": "A taxi to the airport, please.", "description": "Booking a taxi", "difficulty": "beginner"},
            {"sentence": "東京行きの電車は何時に出ますか？", "translation": "What time does the train to Tokyo leave?", "description": "Asking about train", "difficulty": "intermediate"},
            {"sentence": "大阪で乗り換えが必要です。", "translation": "I need to transfer in Osaka.", "description": "Transfer info", "difficulty": "intermediate"},
            {"sentence": "ここで車をレンタルできますか？", "translation": "Can I rent a car here?", "description": "Renting a car", "difficulty": "intermediate"},
            {"sentence": "フライトが三時間遅延しています。接続便に間に合うでしょうか？", "translation": "The flight is delayed by three hours. Will I make my connection?", "description": "Flight delay", "difficulty": "advanced"},
            {"sentence": "荷物が届きません。どこで確認できますか？", "translation": "My luggage hasn't arrived. Where can I check?", "description": "Lost luggage", "difficulty": "advanced"},
            {"sentence": "新幹線で京都までどのくらいかかりますか？", "translation": "How long does it take to Kyoto by bullet train?", "description": "Travel time inquiry", "difficulty": "advanced"}
        ],
        "daily": [
            {"sentence": "もう起きる時間です。", "translation": "It's time to get up.", "description": "Morning routine", "difficulty": "beginner"},
            {"sentence": "今朝はあまり食欲がありません。", "translation": "I don't have much appetite this morning.", "description": "Breakfast conversation", "difficulty": "intermediate"},
            {"sentence": "今日は六時まで仕事があります。", "translation": "I have work until six today.", "description": "Talking about schedule", "difficulty": "intermediate"},
            {"sentence": "週末は何をする予定ですか？", "translation": "What are your plans for the weekend?", "description": "Weekend plans", "difficulty": "intermediate"},
            {"sentence": "今更考えを変えるのは遅すぎます。", "translation": "It's too late to change your mind now.", "description": "Expressing frustration", "difficulty": "advanced"},
            {"sentence": "他の人が何と言っても気にしません。", "translation": "I don't care what others say.", "description": "Expressing opinion", "difficulty": "advanced"},
            {"sentence": "もっと早く計画を立てるべきでした。", "translation": "We should have planned this earlier.", "description": "Planning discussion", "difficulty": "advanced"}
        ]
    },
    "ko": {
        "greetings": [
            {"sentence": "안녕하세요, 어떻게 지내세요?", "translation": "Hello, how are you?", "description": "Casual greeting", "difficulty": "beginner"},
            {"sentence": "좋은 아침이에요. 잘 주무셨어요?", "translation": "Good morning. Did you sleep well?", "description": "Morning greeting", "difficulty": "beginner"},
            {"sentence": "만나서 반갑습니다. 김철수입니다.", "translation": "Nice to meet you. I'm Kim Chulsoo.", "description": "Formal introduction", "difficulty": "beginner"},
            {"sentence": "오랜만이에요. 그동안 잘 지내셨어요?", "translation": "Long time no see. Have you been well?", "description": "Reunion greeting", "difficulty": "intermediate"},
            {"sentence": "여기서 만나다니 정말 반갑네요!", "translation": "What a surprise to meet you here!", "description": "Surprise greeting", "difficulty": "intermediate"},
            {"sentence": "정말 오랜만에 뵙습니다. 건강하시죠?", "translation": "It's been so long. I hope you're healthy?", "description": "Very formal reunion", "difficulty": "advanced"},
            {"sentence": "뵙게 되어 영광입니다. 선생님께 이야기를 많이 들었어요.", "translation": "It's an honor to meet you. I've heard a lot about you from my teacher.", "description": "Very formal greeting", "difficulty": "advanced"}
        ],
        "restaurant": [
            {"sentence": "두 명 자리 부탁합니다.", "translation": "A table for two, please.", "description": "Requesting a table", "difficulty": "beginner"},
            {"sentence": "예약한 김씨입니다.", "translation": "I'm Mr. Kim with a reservation.", "description": "Checking reservation", "difficulty": "beginner"},
            {"sentence": "메뉴판 좀 보여주세요.", "translation": "Please show me the menu.", "description": "Asking for menu", "difficulty": "beginner"},
            {"sentence": "추천 메뉴가 뭐예요?", "translation": "What's the recommended menu?", "description": "Asking for recommendation", "difficulty": "intermediate"},
            {"sentence": "계산 부탁합니다. 카드 되나요?", "translation": "Check please. Do you accept cards?", "description": "Requesting the bill", "difficulty": "intermediate"},
            {"sentence": "죄송한데 알레르기가 있는데 이 음식에 견과류가 들어있나요?", "translation": "Sorry, I have allergies. Does this food contain nuts?", "description": "Allergy inquiry", "difficulty": "advanced"},
            {"sentence": "예약했는데 30분 늦었어요. 아직 가능한가요?", "translation": "I had a reservation but I'm 30 minutes late. Is it still possible?", "description": "Late arrival apology", "difficulty": "advanced"}
        ],
        "shopping": [
            {"sentence": "이거 얼마예요?", "translation": "How much is this?", "description": "Asking price", "difficulty": "beginner"},
            {"sentence": "다른 색깔 있어요?", "translation": "Do you have other colors?", "description": "Asking about colors", "difficulty": "beginner"},
            {"sentence": "이거 입어봐도 돼요?", "translation": "Can I try this on?", "description": "Asking to try on", "difficulty": "beginner"},
            {"sentence": "친구 선물로 뭔가 찾고 있어요.", "translation": "I'm looking for something as a gift for my friend.", "description": "Shopping for a gift", "difficulty": "intermediate"},
            {"sentence": "현금으로 결제하면 할인 되나요?", "translation": "Is there a discount for cash payment?", "description": "Asking for discount", "difficulty": "intermediate"},
            {"sentence": "교환이나 반품 정책이 있나요? 영수증이 필요한가요?", "translation": "Do you have exchange or return policy? Do I need a receipt?", "description": "Return policy inquiry", "difficulty": "advanced"},
            {"sentence": "죄송한데 사이즈가 안 맞아서 한 치수 큰 것으로 교환 가능한가요?", "translation": "Sorry, the size doesn't fit. Can I exchange for one size up?", "description": "Size exchange", "difficulty": "advanced"}
        ],
        "directions": [
            {"sentence": "역이 어디예요?", "translation": "Where is the station?", "description": "Asking for station", "difficulty": "beginner"},
            {"sentence": "여기서 먼가요?", "translation": "Is it far from here?", "description": "Asking about distance", "difficulty": "beginner"},
            {"sentence": "박물관에 어떻게 가나요?", "translation": "How do I get to the museum?", "description": "Asking for directions", "difficulty": "intermediate"},
            {"sentence": "신호등에서 왼쪽으로 도세요.", "translation": "Turn left at the traffic light.", "description": "Giving directions", "difficulty": "intermediate"},
            {"sentence": "이 길로 직진 두 블록 가시면 오른쪽에 보입니다.", "translation": "Go straight two blocks on this road, you'll see it on the right.", "description": "Detailed directions", "difficulty": "advanced"},
            {"sentence": "실례합니다, 근처에 화장실이 있나요?", "translation": "Excuse me, is there a restroom nearby?", "description": "Asking for facilities", "difficulty": "advanced"},
            {"sentence": "실례합니다, 길을 잃었는데 이 근처에 은행이 있나요?", "translation": "Excuse me, I'm lost. Is there a bank nearby?", "description": "Lost and asking", "difficulty": "advanced"}
        ],
        "travel": [
            {"sentence": "공항까지 택시 부탁합니다.", "translation": "A taxi to the airport, please.", "description": "Booking a taxi", "difficulty": "beginner"},
            {"sentence": "서울 가는 기차가 몇 시에 출발하나요?", "translation": "What time does the train to Seoul leave?", "description": "Asking about train", "difficulty": "intermediate"},
            {"sentence": "대전에서 갈아타야 합니다.", "translation": "I need to transfer in Daejeon.", "description": "Transfer info", "difficulty": "intermediate"},
            {"sentence": "여기서 차를 렌트할 수 있나요?", "translation": "Can I rent a car here?", "description": "Renting a car", "difficulty": "intermediate"},
            {"sentence": "비행기가 세 시간 지연됐어요. 연결편을 탈 수 있을까요?", "translation": "The flight is delayed three hours. Can I make my connection?", "description": "Flight delay", "difficulty": "advanced"},
            {"sentence": "짐이 아직 안 나왔어요. 어디서 확인할 수 있나요?", "translation": "My luggage hasn't come out yet. Where can I check?", "description": "Lost luggage", "difficulty": "advanced"},
            {"sentence": "KTX로 부산까지 얼마나 걸려요?", "translation": "How long does it take to Busan by KTX?", "description": "Travel time inquiry", "difficulty": "advanced"}
        ],
        "daily": [
            {"sentence": "이제 일어날 시간이에요.", "translation": "It's time to get up.", "description": "Morning routine", "difficulty": "beginner"},
            {"sentence": "오늘 아침은 appetite이 없어요.", "translation": "I don't have appetite this morning.", "description": "Breakfast conversation", "difficulty": "intermediate"},
            {"sentence": "오늘 여섯 시까지 일해야 해요.", "translation": "I have to work until six today.", "description": "Talking about schedule", "difficulty": "intermediate"},
            {"sentence": "주말에 뭐 할 계획이에요?", "translation": "What are your plans for the weekend?", "description": "Weekend plans", "difficulty": "intermediate"},
            {"sentence": "이제 와서 마음을 바꾸기엔 너무 늦었어요.", "translation": "It's too late to change your mind now.", "description": "Expressing frustration", "difficulty": "advanced"},
            {"sentence": "다른 사람들이 뭐라고 하든 상관없어요.", "translation": "I don't care what others say.", "description": "Expressing opinion", "difficulty": "advanced"},
            {"sentence": "더 일찍 계획을 세웠어야 했는데.", "translation": "We should have planned this earlier.", "description": "Planning discussion", "difficulty": "advanced"}
        ]
    },
    "ru": {
        "greetings": [
            {"sentence": "Здравствуйте, как дела?", "translation": "Hello, how are you?", "description": "Casual greeting", "difficulty": "beginner"},
            {"sentence": "Доброе утро! Вы хорошо спали?", "translation": "Good morning! Did you sleep well?", "description": "Morning greeting", "difficulty": "beginner"},
            {"sentence": "Приятно познакомиться. Меня зовут Алексей.", "translation": "Nice to meet you. My name is Alexey.", "description": "Formal introduction", "difficulty": "beginner"},
            {"sentence": "Давно не виделись! Как у вас дела?", "translation": "Long time no see! How are you doing?", "description": "Reunion greeting", "difficulty": "intermediate"},
            {"sentence": "Какая приятная неожиданность встретить вас здесь!", "translation": "What a pleasant surprise to meet you here!", "description": "Surprise greeting", "difficulty": "intermediate"},
            {"sentence": "Мы так давно не виделись. Надеюсь, у вас всё хорошо?", "translation": "We haven't seen each other in so long. I hope everything is well with you?", "description": "Formal reunion", "difficulty": "advanced"},
            {"sentence": "Очень рад познакомиться. О вас много слышал от преподавателя.", "translation": "Very glad to meet you. I've heard a lot about you from the teacher.", "description": "Very formal greeting", "difficulty": "advanced"}
        ],
        "restaurant": [
            {"sentence": "Столик на двоих, пожалуйста.", "translation": "A table for two, please.", "description": "Requesting a table", "difficulty": "beginner"},
            {"sentence": "Я зарезервировал столик на имя Иванова.", "translation": "I reserved a table under the name Ivanov.", "description": "Checking reservation", "difficulty": "beginner"},
            {"sentence": "Покажите, пожалуйста, меню.", "translation": "Please show me the menu.", "description": "Asking for menu", "difficulty": "beginner"},
            {"sentence": "Что вы порекомендуете?", "translation": "What would you recommend?", "description": "Asking for recommendation", "difficulty": "intermediate"},
            {"sentence": "Счёт, пожалуйста. Можно картой?", "translation": "The check, please. Can I pay by card?", "description": "Requesting the bill", "difficulty": "intermediate"},
            {"sentence": "У меня аллергия. В этом блюде есть орехи?", "translation": "I have allergies. Are there nuts in this dish?", "description": "Allergy inquiry", "difficulty": "advanced"},
            {"sentence": "Извините за опоздание. Мы забронировали столик, но опоздали на тридцать минут.", "translation": "Sorry for being late. We reserved a table but are thirty minutes late.", "description": "Late arrival apology", "difficulty": "advanced"}
        ],
        "shopping": [
            {"sentence": "Сколько это стоит?", "translation": "How much does this cost?", "description": "Asking price", "difficulty": "beginner"},
            {"sentence": "Есть другой цвет?", "translation": "Is there another color?", "description": "Asking about colors", "difficulty": "beginner"},
            {"sentence": "Можно примерить?", "translation": "Can I try it on?", "description": "Asking to try on", "difficulty": "beginner"},
            {"sentence": "Я ищу подарок для друга.", "translation": "I'm looking for a gift for a friend.", "description": "Shopping for a gift", "difficulty": "intermediate"},
            {"sentence": "Есть скидка при оплате наличными?", "translation": "Is there a discount for cash payment?", "description": "Asking for discount", "difficulty": "intermediate"},
            {"sentence": "У вас есть гарантия или возможность возврата?", "translation": "Do you have a warranty or return option?", "description": "Return policy inquiry", "difficulty": "advanced"},
            {"sentence": "Извините, мне не подходит размер. Можно обменять на больший?", "translation": "Excuse me, the size doesn't fit. Can I exchange for a larger one?", "description": "Size exchange", "difficulty": "advanced"}
        ],
        "directions": [
            {"sentence": "Где находится вокзал?", "translation": "Where is the train station?", "description": "Asking for station", "difficulty": "beginner"},
            {"sentence": "Это далеко отсюда?", "translation": "Is it far from here?", "description": "Asking about distance", "difficulty": "beginner"},
            {"sentence": "Как добраться до музея отсюда?", "translation": "How do I get to the museum from here?", "description": "Asking for directions", "difficulty": "intermediate"},
            {"sentence": "Поверните налево на светофоре.", "translation": "Turn left at the traffic light.", "description": "Giving directions", "difficulty": "intermediate"},
            {"sentence": "Идите прямо два квартала, и вы увидите его справа.", "translation": "Walk straight two blocks and you'll see it on the right.", "description": "Detailed directions", "difficulty": "advanced"},
            {"sentence": "Извините, здесь рядом есть общественный туалет?", "translation": "Excuse me, is there a public restroom nearby?", "description": "Asking for facilities", "difficulty": "advanced"},
            {"sentence": "Простите, я заблудился. Подскажите, где здесь банк?", "translation": "Excuse me, I'm lost. Can you tell me where the bank is?", "description": "Lost and asking", "difficulty": "advanced"}
        ],
        "travel": [
            {"sentence": "Мне нужно такси в аэропорт, пожалуйста.", "translation": "I need a taxi to the airport, please.", "description": "Booking a taxi", "difficulty": "beginner"},
            {"sentence": "Во сколько поезд отправляется в Москву?", "translation": "What time does the train to Moscow leave?", "description": "Asking about train", "difficulty": "intermediate"},
            {"sentence": "Мне нужно сделать пересадку в Казани.", "translation": "I need to transfer in Kazan.", "description": "Transfer info", "difficulty": "intermediate"},
            {"sentence": "Где можно арендовать машину?", "translation": "Where can I rent a car?", "description": "Renting a car", "difficulty": "intermediate"},
            {"sentence": "Рейс задерживается на три часа. Успею ли на стыковочный рейс?", "translation": "The flight is delayed three hours. Will I make my connection?", "description": "Flight delay", "difficulty": "advanced"},
            {"sentence": "Мой багаж не прибыл. Где я могу это проверить?", "translation": "My luggage hasn't arrived. Where can I check on this?", "description": "Lost luggage", "difficulty": "advanced"},
            {"sentence": "Сколько времени занимает поездка на поезде до Санкт-Петербурга?", "translation": "How long does the train trip to Saint Petersburg take?", "description": "Travel time inquiry", "difficulty": "advanced"}
        ],
        "daily": [
            {"sentence": "Пора вставать.", "translation": "It's time to get up.", "description": "Morning routine", "difficulty": "beginner"},
            {"sentence": "У меня нет аппетита этим утром.", "translation": "I don't have appetite this morning.", "description": "Breakfast conversation", "difficulty": "intermediate"},
            {"sentence": "Мне нужно работать до шести.", "translation": "I have to work until six.", "description": "Talking about schedule", "difficulty": "intermediate"},
            {"sentence": "Что вы планируете на выходные?", "translation": "What are your plans for the weekend?", "description": "Weekend plans", "difficulty": "intermediate"},
            {"sentence": "Уже слишком поздно менять своё мнение.", "translation": "It's already too late to change your mind.", "description": "Expressing frustration", "difficulty": "advanced"},
            {"sentence": "Мне всё равно, что говорят другие.", "translation": "I don't care what others say.", "description": "Expressing opinion", "difficulty": "advanced"},
            {"sentence": "Нужно было это спланировать раньше.", "translation": "We should have planned this earlier.", "description": "Planning discussion", "difficulty": "advanced"}
        ]
    }
}

# Get all available scenarios
def get_all_scenarios():
    scenarios = set()
    for lang_passages in SHADOW_PASSAGES.values():
        scenarios.update(lang_passages.keys())
    return sorted(list(scenarios))


# Linguistics tips based on Krashen, Swain, Conti, DeKeyser
LINGUISTICS_TIPS = {
    "krashen": [
        "Remember: Low affective filter - stay relaxed and confident!",
        "i+1 principle: We're learning just one new thing at a time.",
        "Acquisition happens naturally when you're relaxed.",
        "Comprehensible input is key - understanding the message matters more than perfect grammar."
    ],
    "swain": [
        "Pushed output: Try to produce language, not just understand it!",
        "Reflection: Think about how you would say something differently.",
        "Notice the gap: Compare your output with native speaker models."
    ],
    "conti": [
        "Spaced repetition: Review words at increasing intervals.",
        "Active recall: Test yourself, don't just re-read!",
        "Interleaving: Mix different types of practice."
    ],
    "dekeyser": [
        "Skill acquisition: Practice makes permanent!",
        "Implicit knowledge comes through deliberate practice.",
        "Auto-correct: Build muscle memory with repetition."
    ]
}


@router.get("/passages")
async def get_passages(language: str = "en", scenario: str = "greetings", difficulty: str = "all"):
    """Get passages for shadow reading practice"""
    lang_code = language[:2].lower() if len(language) > 2 else language.lower()
    passages = SHADOW_PASSAGES.get(lang_code, {}).get(scenario, [])

    if difficulty != "all":
        passages = [p for p in passages if p.get("difficulty") == difficulty]

    return {
        "language": language,
        "scenario": scenario,
        "passages": passages,
        "difficulty": difficulty
    }


@router.get("/scenarios")
async def get_scenarios():
    """Get all available scenarios"""
    all_scenarios = get_all_scenarios()
    return {
        "scenarios": [
            {"id": s, "name": s.capitalize()} for s in all_scenarios
        ]
    }


@router.get("/core-loop")
async def get_core_loop(language: str = "en", theme: str = "greetings"):
    """Get a random passage for the core loop practice"""
    lang_code = language[:2].lower() if len(language) > 2 else language.lower()

    passages = SHADOW_PASSAGES.get(lang_code, {}).get(theme.lower(), [])

    if not passages:
        # Fallback to English
        passages = SHADOW_PASSAGES.get("en", {}).get(theme.lower(), [])

    # Randomly select a passage
    passage = random.choice(passages) if passages else {
        "sentence": "No passage available",
        "translation": "",
        "description": "",
        "difficulty": "beginner"
    }

    # Get linguistics tip
    tip_type = random.choice(["krashen", "swain", "conti", "dekeyser"])

    return {
        "step": "sentence",
        "language": language,
        "theme": theme,
        "sentence": passage["sentence"],
        "translation": passage["translation"],
        "description": passage["description"],
        "difficulty": passage.get("difficulty", "beginner"),
        "linguistics_tip": random.choice(LINGUISTICS_TIPS[tip_type]),
        "tip_type": tip_type
    }


@router.get("/imitate")
async def get_imitate_prompt(language: str = "en", sentence: str = ""):
    """Get imitation step prompt"""
    lang_code = language[:2].lower()

    prompts = {
        "es": f"Escucha y repite: {sentence}",
        "en": f"Listen and repeat: {sentence}",
        "fr": f"Écoutez et répétez: {sentence}",
        "de": f"Hören und wiederholen: {sentence}",
        "ja": f"聞いて繰り返してください: {sentence}",
        "ko": f"듣고 따라하세요: {sentence}",
        "ru": f"Послушайте и повторите: {sentence}"
    }

    return {
        "step": "imitation",
        "prompt": prompts.get(lang_code, prompts["en"]),
        "instruction": "Listen carefully and try to match the pronunciation and intonation.",
        "ready": True
    }


@router.post("/correction")
async def post_correction(
    language: str = Form("en"),
    user_input: str = Form(""),
    target_sentence: str = Form("")
):
    """Get correction/feedback on user's imitation"""
    lang_code = language[:2].lower()
    sentence = target_sentence.lower()

    # Mock analysis - in production, use AI for real feedback
    scores = {
        "pronunciation": random.randint(60, 95),
        "intonation": random.randint(60, 90),
        "fluency": random.randint(65, 95),
        "accuracy": random.randint(70, 95)
    }
    overall_score = int(sum(scores.values()) / len(scores))

    # Generate feedback based on language
    corrections = []

    if lang_code == "es":
        if "hola" in sentence or "cómo" in sentence:
            corrections.append("The 'j' in 'hola' is pronounced like English 'h' - make it softer")
        if "r" in sentence:
            corrections.append("Focus on rolling your 'r' sound")
        if "ñ" in sentence:
            corrections.append("The 'ñ' sound is unique to Spanish - place tongue on roof of mouth")
    elif lang_code == "en":
        if "th" in sentence:
            corrections.append("The 'th' sound - place tongue between teeth, not touching")
        if "how" in sentence or "ow" in sentence:
            corrections.append("The 'ow' diphthong should be a smooth glide")
    elif lang_code == "fr":
        if "r" in sentence:
            corrections.append("The French 'r' comes from the back of your throat")
        if "on" in sentence or "an" in sentence:
            corrections.append("Practice nasal sounds: on, an, en")
    elif lang_code == "de":
        if "ch" in sentence:
            corrections.append("The German 'ch' is a soft sound - like breathing out gently")
        if "ö" in sentence or "ü" in sentence:
            corrections.append("Round your lips for 'ö' and 'ü'")
    elif lang_code == "ja":
        if "っ" in sentence:
            corrections.append("促音(pause): hold the consonant sound briefly before the next syllable")
        if "は" in sentence or "を" in sentence:
            corrections.append("Particles: は is pronounced 'wa', を is pronounced 'o'")
        if "う" in sentence:
            corrections.append("The 'う' sound is subtle - don't overemphasize it")
    elif lang_code == "ko":
        if "ㄹ" in sentence:
            corrections.append("ㄹ is between 'r' and 'l' - tongue taps the roof lightly")
        if "ㅡ" in sentence:
            corrections.append("ㅡ is a flat sound - spread your lips horizontally, no rounding")
        if "ㄲ" in sentence or "ㄸ" in sentence or "ㅃ" in sentence:
            corrections.append("Double consonants (ㄲ,ㄸ,ㅃ) are tense - tighten your throat")
    elif lang_code == "ru":
        if "ы" in sentence:
            corrections.append("The 'ы' sound - tongue back, between 'i' and 'u'")
        if "р" in sentence:
            corrections.append("Russian 'р' is rolled - trill your tongue like Spanish 'rr'")
        if "х" in sentence:
            corrections.append("The 'х' sound is like 'ch' in Scottish 'loch' - from the throat")

    if not corrections:
        corrections = ["Good effort! Keep practicing!", "Focus on clear pronunciation", "Work on smooth delivery"]

    return {
        "step": "correction",
        "score": overall_score,
        "scores": scores,
        "feedback": corrections,
        "encouragement": random.choice([
            "Great effort! Keep practicing!",
            "You're improving! Every attempt helps!",
            "Nice work! Keep going!",
            "Good progress! You're on the right track!"
        ]),
        "recast": f"Native: {target_sentence}"
    }


@router.post("/apply")
async def post_application(
    language: str = Form("en"),
    user_variation: str = Form(""),
    original_sentence: str = Form("")
):
    """Apply/personalize the sentence with user's own version"""
    return {
        "step": "application",
        "saved": True,
        "user_sentence": user_variation,
        "original": original_sentence,
        "message": "Saved to your personal phrase bank!",
        "next_action": "Ready for the next sentence or review your progress."
    }


@router.get("/linguistics")
async def get_linguistics_tip(cycle: int = 0):
    """Get linguistics tip based on practice cycle"""
    tip_type = ["krashen", "swain", "conti", "dekeyser"][cycle % 4]
    return {
        "type": tip_type,
        "tip": random.choice(LINGUISTICS_TIPS[tip_type]),
        "explanation": f"Based on {tip_type.title()}'s research on language acquisition."
    }


@router.get("/")
async def get_practice_records(db: Session = Depends(get_db)):
    """Get all practice records"""
    records = db.query(models.PracticeRecord).filter(
        models.PracticeRecord.user_id == 1
    ).order_by(models.PracticeRecord.created_at.desc()).all()

    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "language": r.language,
            "type": r.type,
            "audio_url": r.audio_url,
            "transcript": r.transcript,
            "score": r.score,
            "feedback": r.feedback,
            "suggestions": r.suggestions,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in records
    ]


@router.post("/analyze")
async def analyze_audio(
    language: str = Form("English"),
    type: str = Form("pronunciation"),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload audio and get AI feedback"""
    upload_dir = os.path.join(os.path.dirname(__file__), "../../uploads")
    os.makedirs(upload_dir, exist_ok=True)

    timestamp = datetime.now().timestamp()
    file_path = os.path.join(upload_dir, f"{timestamp}_{audio.filename}")
    with open(file_path, "wb") as f:
        content = await audio.read()
        f.write(content)

    # Mock AI analysis
    feedback = {
        "pronunciation": random.randint(75, 95),
        "intonation": random.randint(70, 90),
        "fluency": random.randint(75, 90)
    }

    new_record = models.PracticeRecord(
        user_id=1,
        language=language,
        type=type,
        audio_url=f"/uploads/{timestamp}_{audio.filename}",
        transcript="Sample transcribed text",
        score=random.randint(75, 95),
        feedback=feedback,
        suggestions=["Practice the vowel sounds", "Work on sentence stress"]
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    return {
        "id": new_record.id,
        "score": new_record.score,
        "feedback": new_record.feedback,
        "suggestions": new_record.suggestions
    }


@router.get("/{record_id}")
async def get_practice_record(record_id: int, db: Session = Depends(get_db)):
    """Get practice record by ID"""
    record = db.query(models.PracticeRecord).filter(
        models.PracticeRecord.id == record_id,
        models.PracticeRecord.user_id == 1
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    return {
        "id": record.id,
        "language": record.language,
        "score": record.score,
        "transcript": record.transcript,
        "feedback": record.feedback
    }
