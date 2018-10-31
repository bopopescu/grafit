import React, { Component } from "react";
import { BrowserRouter as Router, Route, Link } from 'react-router-dom';
import ArticleList from "./components/articleList";
import ArticleDetail from "./components/articleDetail";
import "./App.css";


let BASE_URL = window.location.toString()

if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" || window.location.hostname === "0.0.0.0") {
  BASE_URL = 'http://' + window.location.hostname + ':8000/'
}

const API = BASE_URL + 'api/v1/'
const AUTH_API = BASE_URL + 'api-token-auth/'
const DEFAULT_QUERY = "articles/"

class App extends Component {
  state = {
    articles: []
  }

  componentDidMount() {

    fetch(AUTH_API,
      {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        method: "POST",
        body: JSON.stringify({ username: 'admin', password: 'admin' })
      })
      .then(response => response.json())
      .then(data => {
        let token = data['token']

        fetch(API + DEFAULT_QUERY, {
          headers: {
            'Authorization': 'Token ' + token
          }
        })
          .then(response => {
            if (response.ok) {
              return response.json();
            } else {
              throw new Error('Something went wrong ...');
            }
          })
          .then(data => this.setState({ articles: data }))
          .catch(error => console.log(error));
      })
      .catch(function (res) { console.log(res) })
  }

  render() {
    return (
      <Router>
        <div className="container">
          <Link to="/">
            <h1 style={{ color: 'black' }}>grafit.io</h1>
          </Link>
          {this.state.articles && (
            <Route exact path="/" render={() => (
              <ArticleList articles={this.state.articles} />)} />
          )}
          {this.state.articles && (
            <Route path="/articles/:articleId" render={({ match }) => {
              return <ArticleDetail article={this.state.articles.find(a => a.id === parseInt(match.params.articleId))} />
            }} />
          )}
        </div>
      </Router>
    );
  }
}

export default App;
