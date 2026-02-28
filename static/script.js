const imgBaseUrl = 'https://image.tmdb.org/t/p/w500';

let currentMood = '';
let displayedMovieIds = [];
let currentMovie = {};

const moodMessages = {
    mutlu: "Gülümsemeni daha da büyütecek filmler seçtim! 😊",
    uzgun: "Bazen sadece durup hissetmek gerekir. Sana eşlik edecek filmler burada. 🌧️",
    ofkeli: "Sakinleşmene yardımcı olacak, öfkeni dindirecek filmler burada. ❤️",
    romantik: "Kalp atışlarını hızlandıracak, aşk dolu hikayeler burada. 💘",
    sikilmis: "Sıkıntını hemen dağıtacak, seni içine çekecek sürükleyici filmler! 🚀",
    heyecan: "Enerjini atabileceğin, soluk soluğa izleyeceğin filmler! 🔥",
    gurur: "İçindeki gücü hissettirecek, ilham veren başarı öyküleri. 🌟",
    yalnizlik: "Kendinle baş başa kalmanın tadını çıkarabileceğin filmler. ☕",
    hayalkirikligi: "Her düşüş yeni bir başlangıçtır. Seni motive edecek ve iyi hissettirecek filmler seçtim. ✨",
    stresli: "Derin bir nefes al. Seni rahatlatacak ve keyfini yerine getirecek filmler burada. 🍃"
};

const moodDisplayNames = {
    mutlu: "Mutlu",
    uzgun: "Üzgün",
    ofkeli: "Öfkeli",
    romantik: "Romantik",
    sikilmis: "Sıkılmış",
    heyecan: "Heyecan",
    gurur: "Gurur",
    yalnizlik: "Yalnızlık",
    hayalkirikligi: "Hayal Kırıklığı",
    stresli: "Stresli"
};

function selectMood(mood) {
    currentMood = mood;
    displayedMovieIds = [];
    const overlay = document.getElementById('recommendation-overlay');
    const chatBox = document.getElementById('chat-box');
    
    const headerTitle = overlay.querySelector('.chat-header h3');
    if (headerTitle) {
        const moodName = moodDisplayNames[mood] || mood.charAt(0).toUpperCase() + mood.slice(1);
        headerTitle.innerText = `ModFlix Asistanı - ${moodName}`;
    }

    chatBox.innerHTML = '';
    overlay.classList.remove('hidden');

    const displayName = moodDisplayNames[mood] || mood.charAt(0).toUpperCase() + mood.slice(1);
    const message = moodMessages[mood] || `${displayName} hissediyorsun demek... Senin için harika önerilerim var! 🎬`;
    addBotMessage(message);

    fetch('/api/recommend', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ mood: mood })
    })
    .then(response => response.json())
    .then(movies => {
        if (movies.length > 0) renderChatCarousel(movies, 'chat-box', { trackIds: true });
        else addBotMessage("Üzgünüm, film bulamadım.");
    });
}

function openAIChat() {
    const overlay = document.getElementById('ai-chat-modal');
    const chatBox = document.getElementById('ai-chat-box');
    
    if (chatBox.innerHTML.trim() === '') {
        addAIBotMessage("Merhaba! Bugün neler yaşadın? Bana anlat, sana en uygun filmi bulayım. 🎬");
    }
    overlay.classList.remove('hidden');
}

async function startChatFromTeaser() {
    const teaserInput = document.getElementById('teaser-input');
    const userText = teaserInput.value.trim();
    
    if (userText === "") return;

    if (!isAuthenticated) {
        openModal('login-modal');
        return;
    }

    const overlay = document.getElementById('ai-chat-modal');
    overlay.classList.remove('hidden');
    
    addAIUserMessage(userText);
    teaserInput.value = '';

    showTypingIndicator('ai-chat-box');

    try {
        const res = await fetch("/api/story-recommendations", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: userText })
        });

        const data = await res.json();
        removeTypingIndicator('ai-chat-box');

        if (data.results && data.results.length > 0) {
            const msg = data.response_message || "İşte hikayene en uygun 5 film önerim:";
            addAIBotMessage(msg);
            renderChatCarousel(data.results, 'ai-chat-box', { isStory: true });
        } else {
            addAIBotMessage("Üzgünüm, hikayene uygun film bulamadım.");
        }
    } catch (error) {
        removeTypingIndicator('ai-chat-box'); 
        addAIBotMessage("Bir hata oluştu, lütfen tekrar dene.");
    }
}

const teaserInputEl = document.getElementById('teaser-input');
if (teaserInputEl) {
    teaserInputEl.addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            startChatFromTeaser();
        }
    });
}

function renderChatCarousel(movies, containerId, options = {}) {
    const { trackIds = false, isStory = false } = options;
    const chatBox = document.getElementById(containerId);
    const carouselDiv = document.createElement('div');
    carouselDiv.className = 'movie-carousel';
    chatBox.appendChild(carouselDiv);

    movies.forEach((movie, index) => {
        const movieId = isStory ? (movie.tmdbId || movie.id) : movie.id;

        if (trackIds && !displayedMovieIds.includes(movieId)) {
            displayedMovieIds.push(movieId);
        }

        setTimeout(() => {
            let posterPath = 'https://placehold.co/140x210?text=No+Image';
            
            if (movie.poster_path && movie.poster_path.trim() !== "") {
                const rawPath = movie.poster_path.trim();
                const path = rawPath.startsWith('/') ? rawPath : '/' + rawPath;
                posterPath = rawPath.startsWith('http') ? rawPath : imgBaseUrl + path;
            } else if (movie.poster) {
                posterPath = movie.poster;
            }
            
            const card = document.createElement('div');
            card.className = 'chat-movie-card';
            card.style.backgroundImage = `url('${posterPath}')`;
            card.onclick = () => openMovieDetails(movieId, movie.overview);

            card.style.opacity = '0';
            card.style.transform = 'scale(0.5)';
            card.style.transition = 'all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
            
            const rating = movie.vote_average ? movie.vote_average.toFixed(1) : '?';
            const textContent = isStory ? `"${movie.reason_tr || ''}"` : (movie.overview || 'Açıklama yok.');
            const textStyle = isStory ? 'font-style: italic;' : '';

            card.innerHTML = `
                <div class="movie-info-overlay">
                    <strong>${movie.title}</strong>
                    <br>⭐ ${rating}
                    <br><br>
                    <span style="font-size: 0.85rem; ${textStyle}">${textContent}</span>
                </div>
            `;
            
            const favBtn = document.createElement('button');
            favBtn.className = 'fav-btn';
            favBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>';
            if (!isStory) favBtn.title = 'Favorilere Ekle';
            
            favBtn.onclick = (e) => {
                e.stopPropagation();
                if (!isAuthenticated) {
                    openModal('login-modal');
                    return;
                }
                favBtn.classList.toggle('active');
                addToFavorites(movieId, movie.title, posterPath);
            };
            card.appendChild(favBtn);
            
            carouselDiv.appendChild(card);
            
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'scale(1)';
            }, 50);

            chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: 'smooth' });
        }, index * 400);
    });
}

function handleUserResponse() {
    const inputField = document.getElementById('user-input');
    const userText = inputField.value.trim();

    if (userText === "") return;

    if (!isAuthenticated) {
        openModal('login-modal');
        return;
    }

    addUserMessage(userText);
    inputField.value = '';

    showTypingIndicator('chat-box');

    fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ 
            message: userText,
            mood: currentMood,
            exclude: displayedMovieIds
        })
    })
    .then(response => response.json())
    .then(data => {
        removeTypingIndicator('chat-box');

        const movies = data.movies || data;
        const message = data.response_message;

        if (message) addBotMessage(message);

        if (movies && movies.length > 0) renderChatCarousel(movies, 'chat-box', { trackIds: true });
        else if (!message) addBotMessage("Üzgünüm, kriterlere uygun film bulamadım.");
    });
}

function handleAIChatResponse() {
    const inputField = document.getElementById('ai-user-input');
    const userText = inputField.value.trim();

    if (userText === "") return;

    if (!isAuthenticated) {
        openModal('login-modal');
        return;
    }

    addAIUserMessage(userText);
    inputField.value = '';

    showTypingIndicator('ai-chat-box');

    fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ 
            message: userText
        })
    })
    .then(response => response.json())
    .then(data => {
        removeTypingIndicator('ai-chat-box');

        const movies = data.movies || data;
        const message = data.response_message;

        if (message) addAIBotMessage(message);

        if (movies && movies.length > 0) renderChatCarousel(movies, 'ai-chat-box', { trackIds: false });
        else if (!message) addAIBotMessage("Üzgünüm, anlattıklarına uygun film bulamadım.");
    });
}

function fetchPopularMovies() {
    fetch('/api/popular')
        .then(response => {
            if (response.ok) return response.json();
            throw new Error('Endpoint not found');
        })
        .then(movies => renderMoviesToContainer(movies, 'popular-movies-container'));
}

function fetchEditorsChoiceMovies() {
    fetch('/api/editors_choice')
        .then(response => {
            if (response.ok) return response.json();
            throw new Error('Endpoint not found');
        })
        .then(movies => renderMoviesToContainer(movies, 'top-rated-movies-container'));
}

function fetchTopRatedMovies() {
    fetch('/api/top_rated')
        .then(response => {
            if (response.ok) return response.json();
            throw new Error('Sunucu hatası veya bağlantı sorunu');
        })
        .then(movies => {
            if (Array.isArray(movies)) {
                renderMoviesToContainer(movies, 'top-rated-movies-container');
            }
        });
}

function switchTopRatedTab(element, type) {
    const chips = element.parentElement.querySelectorAll('.chip');
    chips.forEach(c => c.classList.remove('active'));
    element.classList.add('active');
    
    const container = document.getElementById('top-rated-movies-container');
    if(container) container.innerHTML = '<div class="loading-spinner"></div>';
    
    if (type === 'editor') {
        fetchEditorsChoiceMovies();
    } else {
        fetchTopRatedMovies();
    }
}

function togglePopularGrid(btn, containerId) {
    const container = document.getElementById(containerId);
    const isGrid = container.classList.toggle('grid-view');
    const wrapper = container.closest('.movie-slider-wrapper');
    
    if (isGrid) {
        btn.innerText = 'Kapat';
        if(wrapper) wrapper.querySelectorAll('.scroll-arrow').forEach(el => el.style.display = 'none');
        
        const cards = container.querySelectorAll('.popular-movie-card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.animation = `fadeInUp 0.6s ease forwards ${index * 0.1}s`;
            
            card.addEventListener('animationend', () => {
                card.style.opacity = '';
                card.style.animation = '';
            }, { once: true });
        });
    } else {
        btn.innerText = 'Tümünü Gör';
        if(wrapper) wrapper.querySelectorAll('.scroll-arrow').forEach(el => el.style.display = 'flex');
        
        const cards = container.querySelectorAll('.popular-movie-card');
        cards.forEach(card => {
            card.style.opacity = '';
            card.style.animation = '';
        });
    }
}

function scrollContainer(containerId, direction) {
    const container = document.getElementById(containerId);
    const scrollAmount = 350;
    container.scrollBy({ left: direction * scrollAmount, behavior: 'smooth' });
}

function renderMoviesToContainer(movies, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    
    movies.forEach((movie, index) => {
        let posterPath = 'https://placehold.co/150x225?text=No+Image';
        
        if (movie.poster_path && movie.poster_path.trim() !== "") {
            const rawPath = movie.poster_path.trim();
            const path = rawPath.startsWith('/') ? rawPath : '/' + rawPath;
            posterPath = rawPath.startsWith('http') ? rawPath : imgBaseUrl + path;
        }
        
        const releaseYear = movie.release_date ? movie.release_date.split('-')[0] : '';
        
        const card = document.createElement('div');
        card.className = 'popular-movie-card';
        card.onclick = () => openMovieDetails(movie.id, movie.overview);
        
        const favBtn = document.createElement('button');
        favBtn.className = 'fav-btn';
        favBtn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>';
        favBtn.title = 'Favorilere Ekle';
        favBtn.onclick = (e) => {
            e.stopPropagation();
            if (!isAuthenticated) {
                openModal('login-modal');
                return;
            }
            favBtn.classList.toggle('active');
            addToFavorites(movie.id, movie.title, posterPath);
        };

        let badgeHtml = `<div class="rank-badge">#${index + 1}</div>`;

        card.innerHTML = `
            ${badgeHtml}
            <img src="${posterPath}" alt="${movie.title}">
            <div class="card-overlay">
                <div style="color:white; font-weight:bold; font-size:0.9rem; line-height:1.2;">${movie.title}</div>
                <div class="card-meta">
                    <span>⭐ ${movie.vote_average.toFixed(1)}</span>
                    <span>📅 ${releaseYear}</span>
                </div>
            </div>
        `;
        card.appendChild(favBtn);
        container.appendChild(card);
    });
}

function appendMessage(text, type, containerId) {
    const chatBox = document.getElementById(containerId);
    const div = document.createElement('div');
    div.className = `message ${type}`;
    div.innerText = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function addBotMessage(text) { appendMessage(text, 'bot-message', 'chat-box'); }
function addUserMessage(text) { appendMessage(text, 'user-message', 'chat-box'); }
function addAIBotMessage(text) { appendMessage(text, 'bot-message', 'ai-chat-box'); }
function addAIUserMessage(text) { appendMessage(text, 'user-message', 'ai-chat-box'); }

function showTypingIndicator(chatBoxId) {
    const chatBox = document.getElementById(chatBoxId);
    const div = document.createElement('div');
    div.className = 'message bot-message typing-indicator';
    div.id = 'typing-' + chatBoxId;
    div.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function removeTypingIndicator(chatBoxId) {
    const el = document.getElementById('typing-' + chatBoxId);
    if (el) el.remove();
}

document.getElementById('user-input').addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        handleUserResponse();
    }
});

const aiUserInputEl = document.getElementById('ai-user-input');
if (aiUserInputEl) {
    aiUserInputEl.addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            handleAIChatResponse();
        }
    });
}

function closeRecommendations() {
    const overlay = document.getElementById('recommendation-overlay');
    overlay.classList.add('hidden');
}

function closeAIChat() {
    const overlay = document.getElementById('ai-chat-modal');
    overlay.classList.add('hidden');
}

document.addEventListener("DOMContentLoaded", () => {
    fetchPopularMovies();
    fetchTopRatedMovies();

    document.body.addEventListener('click', (e) => {
        const link = e.target.closest('a');
        if (link && link.href) {
            const path = new URL(link.href).pathname;
            if (['/favorites', '/watched', '/watchlist'].includes(path)) {
                if (!isAuthenticated) {
                    e.preventDefault();
                    openModal('login-modal');
                }
            }
        }
    });

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
            }
        });
    }, { threshold: 0.1 });

    const hiddenElements = document.querySelectorAll('.fade-in-section');
    hiddenElements.forEach((el) => observer.observe(el));
});

async function openMovieDetails(movieId, preferredOverview = null) {
    try {
        const response = await fetch(`/api/movie/${movieId}`);
        const movie = await response.json();
        currentMovie = movie;

        document.getElementById('detail-poster').src = movie.poster_path ? imgBaseUrl + movie.poster_path : 'https://placehold.co/300x450?text=No+Image';
        document.getElementById('detail-title').innerText = movie.title;
        document.getElementById('detail-tagline').innerText = movie.tagline || '';
        document.getElementById('detail-rating').innerText = `⭐ ${movie.vote_average.toFixed(1)}`;
        document.getElementById('detail-runtime').innerText = `⏱️ ${movie.runtime} dk`;
        document.getElementById('detail-date').innerText = `📅 ${movie.release_date ? movie.release_date.split('-')[0] : ''}`;
        
        const countryEl = document.getElementById('detail-country');
        countryEl.innerHTML = '';

        if (movie.production_countries && movie.production_countries.length > 0) {
            const countryCode = movie.production_countries[0].iso_3166_1.toLowerCase();
            const flagImg = document.createElement('img');
            flagImg.src = `https://flagcdn.com/w40/${countryCode}.png`;
            flagImg.style.width = '24px';
            flagImg.style.verticalAlign = 'middle';
            countryEl.appendChild(flagImg);
        }
        
        const genresEl = document.getElementById('detail-genres');
        genresEl.innerHTML = '';
        if (movie.genres) {
            movie.genres.forEach(g => {
                const tag = document.createElement('span');
                tag.className = 'genre-tag';
                tag.innerText = g.name;
                genresEl.appendChild(tag);
            });
        }

        document.getElementById('detail-overview').innerText = preferredOverview || movie.overview;

        const cast = movie.credits.cast.slice(0, 5).map(c => c.name).join(', ');
        document.getElementById('detail-cast').innerText = cast;

        const btnWatched = document.getElementById('btn-watched');
        btnWatched.innerHTML = '👁️ İzledim';
        btnWatched.style.cssText = "padding: 10px 20px; border-radius: 20px; border: 1px solid #ccc; background: white; cursor: pointer; font-weight: 600; transition: all 0.3s;";

        const btnWatchlist = document.getElementById('btn-watchlist');
        btnWatchlist.innerHTML = '📅 İzleyeceğim';
        btnWatchlist.style.cssText = "padding: 10px 20px; border-radius: 20px; border: 1px solid #ccc; background: white; cursor: pointer; font-weight: 600; transition: all 0.3s;";

        document.getElementById('movie-detail-modal').classList.remove('hidden');
    } catch (error) {
        // Error handling
    }
}

function closeMovieDetails() {
    document.getElementById('movie-detail-modal').classList.add('hidden');
}

function openModal(modalId) {
    document.getElementById(modalId).classList.remove('hidden');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

function switchModal(closeId, openId) {
    closeModal(closeId);
    openModal(openId);
}

function toggleMenu() {
    document.getElementById("sidebar-menu").classList.toggle("open");
    document.getElementById("sidebar-overlay").classList.toggle("active");
}

document.addEventListener('keydown', function(event) {
    if (event.key === "Escape") {
        const sidebar = document.getElementById("sidebar-menu");
        if (sidebar.classList.contains('open')) {
            toggleMenu();
        }
    }
});

function addToFavorites(movieId, title, posterPath) {
    fetch('/api/add_favorite', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            movie_id: movieId,
            title: title,
            poster_path: posterPath
        })
    })
    .then(response => response.json())
    .then(data => {});
}

function toggleWatchlistFromModal() {
    if (!currentMovie || !currentMovie.id) return;

    fetch('/api/add_watchlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            movie_id: currentMovie.id,
            title: currentMovie.title,
            poster_path: currentMovie.poster_path
        })
    })
    .then(response => response.json())
    .then(data => {
        const btn = document.getElementById('btn-watchlist');
        if (data.action === 'added') {
            btn.innerHTML = '✔ Listede';
            btn.style.background = '#E8A6B8';
            btn.style.color = 'white';
            btn.style.borderColor = '#E8A6B8';
        } else {
            btn.innerHTML = '📅 İzleyeceğim';
            btn.style.background = 'white';
            btn.style.color = 'black';
            btn.style.borderColor = '#ccc';
        }
    });
}

function toggleFavoriteInPage(movieId, btnElement) {
    fetch('/api/add_favorite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ movie_id: movieId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.action === 'removed') {
            const card = btnElement.closest('.fav-card');
            card.style.transform = 'scale(0.9)';
            card.style.opacity = '0';
            setTimeout(() => {
                card.remove();
                if (document.querySelectorAll('.fav-card').length === 0) {
                    location.reload();
                }
            }, 300);
        }
    });
}

function toggleWatchlistInPage(movieId, btnElement) {
    fetch('/api/add_watchlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ movie_id: movieId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.action === 'removed') {
            const card = btnElement.closest('.watchlist-card');
            card.style.transform = 'scale(0.9)';
            card.style.opacity = '0';
            setTimeout(() => {
                card.remove();
                if (document.querySelectorAll('.watchlist-card').length === 0) {
                    location.reload();
                }
            }, 300);
        }
    });
}

function toggleWatchedFromModal() {
    if (!currentMovie || !currentMovie.id) return;

    fetch('/api/add_watched', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            movie_id: currentMovie.id,
            title: currentMovie.title,
            poster_path: currentMovie.poster_path
        })
    })
    .then(response => response.json())
    .then(data => {
        const btn = document.getElementById('btn-watched');
        if (data.action === 'added') {
            btn.innerHTML = '✔ İzlendi';
            btn.style.background = '#E8A6B8';
            btn.style.color = 'white';
            btn.style.borderColor = '#E8A6B8';
        } else {
            btn.innerHTML = '👁️ İzledim';
            btn.style.background = 'white';
            btn.style.color = 'black';
            btn.style.borderColor = '#ccc';
        }
    });
}
